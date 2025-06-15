import inspect
from typing import Any, Dict, List, Optional, TypeVar

from django.db.models import Model
from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.utils import model_meta
from rest_framework_dataclasses.serializers import DataclassSerializer
from rest_framework_dataclasses.types import Dataclass

from air_drf_relation.context_builder import set_empty_request_in_kwargs
from air_drf_relation.extra_kwargs import ExtraKwargsFactory
from air_drf_relation.fields import AirRelatedField
from air_drf_relation.preload_objects_manager import PreloadObjectsManager
from air_drf_relation.queryset_optimization import optimize_queryset
from air_drf_relation.utils import stringify_uuids

T = TypeVar('T', bound=Dataclass)


class AirSerializer(serializers.Serializer):
    """
    Base serializer with preloading support and UUID stringification.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        self._preload_objects_manager: Optional[PreloadObjectsManager] = None
        self.preload_objects: Optional[bool] = kwargs.pop('preload_objects', None)
        super().__init__(*args, **kwargs)

    def update(self, instance: Any, validated_data: Dict[str, Any]) -> Any:
        """Update method must be implemented in subclasses."""
        raise NotImplementedError('`update()` must be implemented.')

    def create(self, validated_data: Dict[str, Any]) -> Any:
        """Create method must be implemented in subclasses."""
        raise NotImplementedError('`create()` must be implemented.')

    def is_valid(self, raise_exception: bool = False) -> bool:
        """
        Validate data and initialize preload manager if needed.

        Args:
            raise_exception: Whether to raise exception on validation error

        Returns:
            True if data is valid
        """
        if self.preload_objects is not False:
            self._preload_objects_manager = PreloadObjectsManager.get_preload_objects_manager(self).init()
        return super().is_valid(raise_exception=raise_exception)

    def to_representation(self, instance: Any) -> Dict[str, Any]:
        """Convert instance to representation with UUID stringification."""
        data = super().to_representation(instance)
        return stringify_uuids(data)

    @classmethod
    def many_init(cls, *args: Any, **kwargs: Any) -> 'AirListSerializer':
        """Initialize list serializer with optimization."""
        cls._ensure_meta_with_list_serializer()
        serializer = super().many_init(*args, **kwargs)

        if cls._should_optimize_queryset(serializer):
            serializer.instance = optimize_queryset(serializer.instance, serializer.child)

        return serializer

    @classmethod
    def _ensure_meta_with_list_serializer(cls) -> None:
        """Ensure Meta class exists with list_serializer_class."""
        meta = getattr(cls, 'Meta', None)
        if not meta:

            class Meta:
                pass

            meta = Meta()
            setattr(cls, 'Meta', meta)

        if not hasattr(meta, 'list_serializer_class'):
            setattr(meta, 'list_serializer_class', AirListSerializer)

    @staticmethod
    def _should_optimize_queryset(serializer: 'AirListSerializer') -> bool:
        """Check if queryset should be optimized."""
        return (
            hasattr(serializer, 'parent')
            and serializer.parent is None
            and serializer.child
            and hasattr(serializer.child, 'optimize_queryset')
            and serializer.child.optimize_queryset
        )


class AirModelSerializer(serializers.ModelSerializer, AirSerializer):
    class Meta:
        model = None
        fields = ()
        read_only_fields = ()
        write_only_fields = ()
        extra_kwargs = {}
        optimize_queryset = True

    def __init__(self, *args, **kwargs):
        self._extract_init_params(kwargs)
        self._setup_context_if_needed(kwargs)
        self._setup_action_and_user(kwargs)
        self.extra_kwargs = self._get_extra_kwargs()
        self._update_extra_kwargs_in_fields()

        super().__init__(*args, **kwargs)
        self._update_fields()

    def _extract_init_params(self, kwargs: Dict[str, Any]) -> None:
        """Extract and store initialization parameters."""
        self.action = kwargs.pop('action', None)
        self.user = kwargs.pop('user', None)
        self.optimize_queryset = kwargs.pop('optimize_queryset', getattr(self.Meta, 'optimize_queryset', True))
        self._initial_extra_kwargs = kwargs.pop('extra_kwargs', {})

    def _setup_context_if_needed(self, kwargs: Dict[str, Any]) -> None:
        """Setup context if not provided."""
        if 'context' not in kwargs:
            set_empty_request_in_kwargs(kwargs=kwargs)

    def _setup_action_and_user(self, kwargs: Dict[str, Any]) -> None:
        """Setup action and user from context if not provided."""
        if not self.action:
            self._set_action_from_view(kwargs)
        if not self.user:
            self._set_user_from_request(kwargs)

    def _set_action_from_view(self, kwargs: Dict[str, Any]) -> None:
        """Extract action from view context."""
        context = kwargs.get('context')
        if context and context.get('view'):
            self.action = context['view'].action

    def _set_user_from_request(self, kwargs: Dict[str, Any]) -> None:
        """Extract authenticated user from request context."""
        context = kwargs.get('context')
        if not context:
            return

        request = context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            self.user = request.user

    def _get_extra_kwargs(self) -> Dict[str, Any]:
        """Generate extra_kwargs using factory."""
        data = {'extra_kwargs': self._initial_extra_kwargs}
        extra_kwargs = ExtraKwargsFactory(meta=self.Meta, data=data, action=self.action).init().extra_kwargs

        self._clean_custom_extra_kwargs()
        return extra_kwargs

    def _update_extra_kwargs_in_fields(self) -> None:
        """Apply extra_kwargs to field definitions."""
        for field_name, field_kwargs in self.extra_kwargs.items():
            field = self.fields.fields.get(field_name)
            if field:
                field.__dict__.update(field_kwargs)
                field._kwargs = {**field._kwargs, **field_kwargs}

    def _clean_custom_extra_kwargs(self) -> None:
        """Remove custom kwargs that shouldn't be passed to DRF."""
        if not hasattr(self.Meta, 'extra_kwargs'):
            return

        for field_kwargs in self.Meta.extra_kwargs.values():
            field_kwargs.pop('pk_only', None)
            field_kwargs.pop('hidden', None)

    def _update_fields(self) -> None:
        """Update and configure serializer fields."""
        if not hasattr(self.Meta, 'model'):
            return

        self._remove_hidden_fields()
        self._configure_related_fields()

    def _remove_hidden_fields(self) -> None:
        """Remove fields marked as hidden."""
        hidden_fields = [name for name, field in self.fields.items() if getattr(field, 'hidden', False)]
        for field_name in hidden_fields:
            del self.fields[field_name]

    def _configure_related_fields(self) -> None:
        """Configure AirRelatedField instances."""
        model_info = model_meta.get_field_info(self.Meta.model)

        for field_name, field in self.fields.items():
            if not isinstance(field, AirRelatedField):
                continue

            field.parent = self
            model_field = model_info.relations[field_name].model_field

            if not model_field.editable:
                field.read_only = True
                continue

            if model_field.null:
                self._set_nullable_field_defaults(field)

    def _set_nullable_field_defaults(self, field: AirRelatedField) -> None:
        """Set defaults for nullable fields."""
        if field._kwargs.get('required') is None:
            field.required = False
        if field._kwargs.get('allow_null') is None:
            field.allow_null = True

    def update_or_create(self, instance: Optional[Model], validated_data: Dict[str, Any]) -> Model:
        """Update existing instance or create new one."""
        super_class = super()
        return super_class.create(validated_data) if not instance else super_class.update(instance, validated_data)

    def create(self, validated_data: Dict[str, Any]) -> Model:
        """Create new instance."""
        return self.update_or_create(None, validated_data)

    def update(self, instance: Model, validated_data: Dict[str, Any]) -> Model:
        """Update existing instance."""
        return self.update_or_create(instance, validated_data)

    def is_valid(self, raise_exception: bool = False) -> bool:
        """Validate with queryset filtering."""
        self._filter_queryset_by_fields()
        return super().is_valid(raise_exception=raise_exception)

    def _filter_queryset_by_fields(self) -> None:
        """Apply dynamic queryset filtering for related fields."""
        related_fields = self._get_related_fields()

        for field_name, field in related_fields.items():
            if not self.initial_data.get(field_name):
                continue

            function_name = self._get_queryset_function_name(field, field_name)
            if (
                function_name
                and hasattr(self.__class__, function_name)
                and callable(getattr(self.__class__, function_name))
            ):
                field.queryset = self._call_queryset_function(function_name, field.queryset)

    def _call_queryset_function(self, function_name: str, queryset: Any) -> Any:
        """Call queryset function with automatic self parameter detection."""
        func = getattr(self.__class__, function_name)

        try:
            sig = inspect.signature(func)
            has_self = 'self' in sig.parameters
            return func(self, queryset=queryset) if has_self else func(queryset=queryset)
        except (TypeError, ValueError):
            pass

    def _get_queryset_function_name(self, field: serializers.Field, field_name: str) -> str:
        """Get the name of the queryset filtering function."""
        field_name = field.field_name
        if field_name in self.extra_kwargs:
            if self.extra_kwargs[field_name].get('queryset_function_disabled'):
                return None
            if 'queryset_function_name' in self.extra_kwargs[field_name]:
                return self.extra_kwargs[field_name]['queryset_function_name']
        if isinstance(field, AirRelatedField):
            if field.queryset_function_disabled:
                return None
            if field.queryset_function_name:
                return field.queryset_function_name
        return f'queryset_{field_name}'

    def _get_related_fields(self) -> Dict[str, serializers.Field]:
        """Get all related fields from the serializer."""
        return {
            name: field
            for name, field in self.fields.items()
            if isinstance(field, (AirRelatedField, PrimaryKeyRelatedField))
        }

    def __new__(cls, *args, **kwargs):
        """Handle many=True initialization."""
        if kwargs.pop('many', False):
            if 'context' not in kwargs:
                set_empty_request_in_kwargs(kwargs=kwargs)
            return cls.many_init(*args, **kwargs)
        return super().__new__(cls, *args, **kwargs)

    def to_representation(self, instance: Any) -> Dict[str, Any]:
        """Convert to representation with optional queryset optimization."""
        if getattr(self, 'parent') is None and self.optimize_queryset:
            instance = optimize_queryset(instance, self)
        return super().to_representation(instance)


class AirListSerializer(serializers.ListSerializer):
    """
    Enhanced ListSerializer with preloading support.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        self.preload_objects: Optional[bool] = kwargs.pop('preload_objects', None)
        super().__init__(*args, **kwargs)
        self._preload_objects_manager: Optional[PreloadObjectsManager] = None

    def is_valid(self, raise_exception: bool = False) -> bool:
        """Validate data with preload manager initialization."""
        if self._should_initialize_preload_manager():
            self._preload_objects_manager = PreloadObjectsManager.get_preload_objects_manager(self).init()
        return super().is_valid(raise_exception=raise_exception)

    def _should_initialize_preload_manager(self) -> bool:
        """Check if preload manager should be initialized."""
        return self.preload_objects is not False and getattr(self.child, 'preload_objects', None) is not False

    def update(self, instance: List[Model], validated_data: List[Dict[str, Any]]) -> List[Model]:
        """Update list of instances."""
        return super().update(instance, validated_data)


class AirEmptySerializer(AirSerializer):
    """
    Empty serializer base class for serializers without create/update logic.
    """

    def update(self, instance: Any, validated_data: Dict[str, Any]) -> Any:
        """Update is not implemented for empty serializer."""
        raise NotImplementedError('Update is not implemented for AirEmptySerializer')

    def create(self, validated_data: Dict[str, Any]) -> Any:
        """Create is not implemented for empty serializer."""
        raise NotImplementedError('Create is not implemented for AirEmptySerializer')


class AirDynamicSerializer(AirEmptySerializer):
    """
    Dynamic serializer that accepts field definitions at runtime.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        values = kwargs.pop('values')

        if not isinstance(values, dict):
            raise TypeError('values should be dict.')

        self._add_dynamic_fields(values)
        super().__init__(*args, **kwargs)

    def _add_dynamic_fields(self, values: Dict[str, serializers.Field]) -> None:
        """Add dynamic fields to the serializer."""
        for field_name, field_instance in values.items():
            self.fields.fields[field_name] = field_instance
            field_instance.field_name = field_name
            field_instance.source_attrs = [field_name]


class AirDataclassSerializer(DataclassSerializer):
    """
    Enhanced DataclassSerializer with improved field handling and validation.

    Provides better support for partial updates and nested dataclass serialization.
    """

    def to_internal_value(self, data: Dict[str, Any]) -> T:
        """
        Convert input data to dataclass instance with field preservation.

        Args:
            data: Input data dictionary

        Returns:
            Validated dataclass instance with preserved existing field values
        """
        instance = super().to_internal_value(data)
        self._preserve_missing_field_values(instance, data)
        return instance

    def run_validation(self, data: Any = empty) -> T:
        """
        Run validation with proper instance handling for nested serializers.

        Args:
            data: Data to validate

        Returns:
            Validated dataclass instance
        """
        self._setup_nested_instance()
        return super().run_validation(data)

    def to_representation(self, instance: Any) -> Dict[str, Any]:
        """
        Convert dataclass instance to dictionary representation.

        Args:
            instance: Dataclass instance or dictionary to represent

        Returns:
            Dictionary representation with proper field handling
        """
        if instance is not None and isinstance(instance, dict):
            self._ensure_writable_fields_in_dict(instance)

        return super().to_representation(instance)

    def _preserve_missing_field_values(self, instance: T, data: Dict[str, Any]) -> None:
        """
        Preserve values for fields not present in input data.

        Args:
            instance: Target dataclass instance
            data: Input data dictionary
        """
        dataclass = self.Meta.dataclass
        value_keys = data.keys()

        for key in instance.__dict__.keys():
            if key not in value_keys or getattr(instance, key) == empty:
                value = self._get_field_default_value(key, dataclass)
                setattr(instance, key, value)

    def _get_field_default_value(self, field_name: str, dataclass: type) -> Any:
        """
        Get default value for a field from existing instance or dataclass.

        Args:
            field_name: Name of the field
            dataclass: Dataclass type

        Returns:
            Default value for the field
        """
        if self.instance:
            return getattr(self.instance, field_name, None)
        return getattr(dataclass, field_name, None)

    def _setup_nested_instance(self) -> None:
        """Setup instance for nested serializer from parent instance."""
        if self.parent and getattr(self.parent, 'instance', None):
            self.instance = getattr(self.parent.instance, self.source, None)

    def _ensure_writable_fields_in_dict(self, instance: Dict[str, Any]) -> None:
        """
        Ensure all writable fields are present in dictionary representation.

        Args:
            instance: Dictionary instance to update
        """
        for field in self._writable_fields:
            if field.field_name not in instance:
                instance[field.field_name] = None
