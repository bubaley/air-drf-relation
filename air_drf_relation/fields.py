import json
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Optional, Type, Union

from dacite import from_dict
from django.db import models
from django.db.models import Model
from rest_framework.relations import Field, PrimaryKeyRelatedField
from rest_framework.serializers import BaseSerializer

from air_drf_relation.utils import get_pk_from_data


class AirRelatedField(PrimaryKeyRelatedField):
    """
    A custom related field that can work both as a PK field and as a serializer field.
    Supports dynamic queryset functions and hidden field functionality.
    """

    def __init__(self, serializer: Type[BaseSerializer], **kwargs: Any):
        self.serializer = serializer
        self.pk_only = kwargs.pop('pk_only', False)
        self.hidden = kwargs.pop('hidden', False)
        self.queryset_function_name = kwargs.pop('queryset_function_name', None)
        self.queryset_function_disabled = kwargs.pop('queryset_function_disabled', False)
        self.parent: Optional[BaseSerializer] = None

        # Remove as_serializer from kwargs as it's handled in __new__
        kwargs.pop('as_serializer', None)

        self._setup_queryset(kwargs)
        super().__init__(**kwargs)

    def _setup_queryset(self, kwargs: Dict[str, Any]) -> None:
        """Setup queryset based on read_only status and provided arguments."""
        if not kwargs.get('read_only'):
            self.queryset = kwargs.pop('queryset', None)
            if not self.queryset:
                self.queryset = self.serializer.Meta.model.objects
        else:
            self.queryset_function_disabled = True

    def __new__(
        cls, serializer: Type[BaseSerializer], *args: Any, **kwargs: Any
    ) -> Union['AirRelatedField', BaseSerializer]:
        """
        Create either AirRelatedField instance or serializer instance based on as_serializer flag.
        """
        if kwargs.pop('as_serializer', False):
            return serializer(*args, **kwargs)
        return super().__new__(cls, serializer, *args, **kwargs)

    def use_pk_only_optimization(self) -> bool:
        """Check if field should use primary key only optimization."""
        return self.pk_only

    def to_internal_value(self, data: Any) -> Any:
        """Convert input data to internal value, extracting PK if necessary."""
        if self.queryset and hasattr(self.queryset, 'model'):
            pk_field_name = self.queryset.model._meta.pk.name
            data = get_pk_from_data(data, pk_field_name)
        return super().to_internal_value(data)

    def to_representation(self, value: Model) -> Union[Dict[str, Any], Any]:
        """
        Convert model instance to representation.
        Returns serialized data if not pk_only, otherwise returns primary key.
        """
        if not self.pk_only:
            serializer = self.serializer(value, context=self.context)
            serializer.parent = self.parent
            return serializer.data
        return value.pk


class AirAnyField(Field):
    """
    A field that accepts any value and returns it as-is.
    Useful for dynamic data that doesn't need validation or transformation.
    """

    def to_representation(self, value: Any) -> Any:
        """Return value as-is for representation."""
        return value

    def to_internal_value(self, data: Any) -> Any:
        """Return data as-is for internal processing."""
        return data


class AirDataclassField(models.JSONField):
    """
    A Django model field that stores dataclass instances as JSON.
    Automatically serializes dataclass to JSON when saving and deserializes JSON to dataclass when loading.
    """

    def __init__(self, data_class: Type, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the field with a dataclass type.

        Args:
            data_class: The dataclass type to serialize/deserialize
        """
        if not hasattr(data_class, '__dataclass_fields__'):
            raise ValueError(f'data_class must be a dataclass, got {data_class}')

        self.data_class = data_class
        super().__init__(*args, **kwargs)

    def deconstruct(self) -> tuple[str, str, tuple, Dict[str, Any]]:
        """Return field deconstruction for migrations."""
        name, path, args, kwargs = super().deconstruct()
        kwargs['data_class'] = self.data_class
        return name, path, args, kwargs

    def from_db_value(self, value: Optional[str], expression: Any, connection: Any) -> Optional[Any]:
        """Convert database value to Python dataclass instance."""
        if value is None:
            return None

        return self._deserialize_value(value)

    def to_python(self, value: Any) -> Optional[Any]:
        """Convert value to Python dataclass instance."""
        if isinstance(value, self.data_class) or value is None:
            return value

        if isinstance(value, str):
            return self._deserialize_value(value)

        # Handle dict input (e.g., from forms)
        if isinstance(value, dict):
            return self._create_dataclass_from_dict(value)

        return value

    def get_prep_value(self, value: Any) -> Optional[Dict[str, Any]]:
        """Convert Python dataclass instance to database value."""
        if value is None:
            return None

        if not is_dataclass(value):
            if hasattr(self, 'default') and callable(self.default):
                return self.default()
            return None

        return asdict(value)

    def _deserialize_value(self, value: str) -> Optional[Any]:
        """
        Deserialize JSON string to dataclass instance.

        Args:
            value: JSON string to deserialize

        Returns:
            Dataclass instance or None if deserialization fails
        """
        try:
            data = json.loads(value)
            if data is None:
                return None
            return self._create_dataclass_from_dict(data)
        except (json.JSONDecodeError, TypeError, ValueError):
            # Log the error if logging is configured
            # For now, return None to handle gracefully
            return None

    def _create_dataclass_from_dict(self, data: Dict[str, Any]) -> Optional[Any]:
        """
        Create dataclass instance from dictionary.

        Args:
            data: Dictionary data to convert to dataclass

        Returns:
            Dataclass instance or None if creation fails
        """
        try:
            return from_dict(data_class=self.data_class, data=data)
        except (TypeError, ValueError):
            # Log the error if logging is configured
            # For now, return None to handle gracefully
            return None
