from typing import Any, Dict, Optional, Type, Union

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
