import json
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Optional, Type

from dacite import from_dict
from django.db import models


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
