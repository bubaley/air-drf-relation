import json
import logging
from typing import Any, Dict

from django.core.serializers.json import Serializer as DjangoSerializer
from django.db import models

from air_drf_relation.model_fields import AirDataclassField

logger = logging.getLogger(__name__)


class Serializer(DjangoSerializer):
    """
    Custom Django serializer with enhanced support for AirDataclassField.

    This serializer extends the default Django JSON serializer to properly
    handle AirDataclassField instances by converting them to their default
    dictionary representation during serialization.
    """

    def get_dump_object(self, obj: models.Model) -> Dict[str, Any]:
        """
        Convert a Django model instance to a serializable dictionary.

        This method extends the default Django serialization to handle
        AirDataclassField instances specially, converting them to their
        default dictionary representation using JSON serialization.

        Args:
            obj: Django model instance to serialize.

        Returns:
            Dictionary containing the serialized model data.

        Raises:
            ValueError: If the object cannot be serialized.
            TypeError: If field value conversion fails.
        """
        try:
            # Build base data structure
            data = {'model': str(obj._meta)}

            # Handle primary key
            if not self.use_natural_primary_keys or not hasattr(obj, 'natural_key'):
                data['pk'] = self._value_from_field(obj, obj._meta.pk)

            # Process model fields with special handling for AirDataclassField
            self._process_model_fields(obj)

            data['fields'] = self._current
            return data

        except Exception as e:
            logger.error(
                f'Failed to serialize object {obj.__class__.__name__} with pk={getattr(obj, "pk", "unknown")}: {e}'
            )
            raise ValueError(f'Serialization failed for {obj.__class__.__name__}: {e}') from e

    def _process_model_fields(self, obj: models.Model) -> None:
        """
        Process all model fields with special handling for AirDataclassField.

        Args:
            obj: Django model instance to process.

        Raises:
            TypeError: If AirDataclassField value cannot be converted to JSON.
        """
        for field in obj._meta.fields:
            if isinstance(field, AirDataclassField):
                self._handle_dataclass_field(field)

    def _handle_dataclass_field(self, field: AirDataclassField) -> None:
        """
        Handle serialization of AirDataclassField.

        Converts the dataclass instance to its default dictionary representation
        and stores it as JSON string in the current serialization context.

        Args:
            field: AirDataclassField instance to process.

        Raises:
            TypeError: If the field value cannot be converted to JSON.
            AttributeError: If the field value doesn't have default_dict method.
        """
        try:
            field_value = self._current.get(field.name)
            if field_value is not None:
                # Convert dataclass to dictionary and then to JSON
                if hasattr(field_value, 'default_dict'):
                    dict_value = field_value.default_dict()
                else:
                    # Fallback to standard dictionary conversion
                    from dataclasses import asdict, is_dataclass

                    dict_value = asdict(field_value) if is_dataclass(field_value) else field_value

                self._current[field.name] = json.dumps(dict_value, ensure_ascii=False)

        except (TypeError, AttributeError, ValueError) as e:
            logger.warning(
                f"Failed to serialize AirDataclassField '{field.name}': {e}. Field will be serialized as None."
            )
            self._current[field.name] = None

    def _value_from_field(self, obj: models.Model, field: models.Field) -> Any:
        """
        Enhanced field value extraction with error handling.

        Args:
            obj: Model instance.
            field: Field to extract value from.

        Returns:
            Field value or None if extraction fails.
        """
        try:
            return super()._value_from_field(obj, field)
        except Exception as e:
            logger.warning(f"Failed to extract value from field '{field.name}' of {obj.__class__.__name__}: {e}")
            return None
