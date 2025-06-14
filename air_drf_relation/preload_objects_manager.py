from hashlib import blake2s
from typing import Any, Dict, List, Optional, Type, Union

from django.db.models import Model, QuerySet
from rest_framework import fields, serializers
from rest_framework.relations import PrimaryKeyRelatedField

from .settings import air_drf_relation_settings


class PreloadObjectsManager:
    """
    Manager for preloading related objects to optimize serializer performance.
    Collects related object PKs from serializer data and preloads them in batches.
    """

    def __init__(self, serializer: serializers.BaseSerializer):
        self.preloaded_objects: Dict[str, Union[List[Model], QuerySet]] = {}
        self._objects_for_preload: Dict[str, Dict[str, Any]] = {}
        self._serializer = self._get_base_serializer(serializer)

    @staticmethod
    def _get_base_serializer(serializer: serializers.BaseSerializer) -> serializers.BaseSerializer:
        """Get the base serializer from ListSerializer if needed."""
        return serializer.child if isinstance(serializer, serializers.ListSerializer) else serializer

    @staticmethod
    def get_preload_objects_manager(serializer: serializers.BaseSerializer) -> 'PreloadObjectsManager':
        """
        Get or create PreloadObjectsManager for the given serializer.

        Args:
            serializer: The serializer to get manager for

        Returns:
            PreloadObjectsManager instance
        """
        manager = PreloadObjectsManager.find_preload_objects_manager(serializer)
        return manager if manager else PreloadObjectsManager(serializer)

    def init(self) -> Optional['PreloadObjectsManager']:
        """
        Initialize preloading by collecting PKs and executing queries.

        Returns:
            Self if preloading is enabled, None otherwise
        """
        if not air_drf_relation_settings.get('USE_PRELOAD'):
            return None

        self._collect_objects_for_preload(self._serializer, self._serializer.initial_data)
        self._execute_preload_queries()
        return self

    def _collect_objects_for_preload(self, serializer: serializers.BaseSerializer, data: Any) -> None:
        """
        Recursively collect objects that need to be preloaded.

        Args:
            serializer: Current serializer being processed
            data: Data to extract PKs from
        """
        if not data:
            return

        data_list = data if isinstance(data, list) else [data]

        for item in data_list:
            self._process_serializer_fields(serializer, item)

    def _process_serializer_fields(self, serializer: serializers.BaseSerializer, data_item: Any) -> None:
        """
        Process all fields in the serializer to collect related object PKs.

        Args:
            serializer: Serializer containing fields to process
            data_item: Single data item to extract values from
        """
        for field in serializer._writable_fields:
            field_type = type(field)

            if self._is_pk_related_field(field_type):
                self._handle_pk_related_field(field, data_item)
            elif self._is_many_related_field(field_type):
                self._handle_many_related_field(field, data_item)
            elif self._is_nested_serializer(field_type):
                self._handle_nested_serializer(field, data_item)

    def _is_pk_related_field(self, field_type: Type) -> bool:
        """Check if field is a PrimaryKeyRelatedField."""
        return issubclass(field_type, serializers.PrimaryKeyRelatedField)

    def _is_many_related_field(self, field_type: Type) -> bool:
        """Check if field is a ManyRelatedField."""
        return issubclass(field_type, serializers.ManyRelatedField)

    def _is_nested_serializer(self, field_type: Type) -> bool:
        """Check if field is a nested serializer."""
        return issubclass(field_type, serializers.Serializer) or (
            issubclass(field_type, serializers.ListSerializer) and hasattr(field_type, 'child')
        )

    def _handle_pk_related_field(self, field: serializers.PrimaryKeyRelatedField, data_item: Any) -> None:
        """Handle PrimaryKeyRelatedField by collecting its value."""
        value = self._get_field_value(field, data_item)
        if hasattr(field, 'queryset'):
            self._append_object_pks(field.queryset, value)

    def _handle_many_related_field(self, field: serializers.ManyRelatedField, data_item: Any) -> None:
        """Handle ManyRelatedField by collecting its values."""
        value = field.get_value(data_item)
        if hasattr(field, 'child_relation') and hasattr(field.child_relation, 'queryset'):
            self._append_object_pks(field.child_relation.queryset, value)

    def _handle_nested_serializer(self, field: serializers.BaseSerializer, data_item: Any) -> None:
        """Handle nested serializers recursively."""
        field_value = self._get_nested_field_value(field, data_item)

        if isinstance(field, serializers.ListSerializer) and hasattr(field, 'child'):
            self._collect_objects_for_preload(field.child, field_value)
        else:
            self._collect_objects_for_preload(field, field_value)

    def _get_field_value(self, field: serializers.Field, data_item: Any) -> Any:
        """Get field value from data item."""
        return field.get_value(data_item) if isinstance(data_item, dict) else data_item

    def _get_nested_field_value(self, field: serializers.Field, data_item: Any) -> Any:
        """Get nested field value from data item."""
        return data_item.get(field.field_name) if isinstance(data_item, dict) else None

    def _execute_preload_queries(self) -> None:
        """Execute all collected preload queries."""
        for query_hash, data in self._objects_for_preload.items():
            pks = data['pks']
            queryset = data['queryset']

            self.preloaded_objects[query_hash] = list(queryset.filter(pk__in=list(set(pks)))) if pks else []

    def _append_object_pks(self, queryset: QuerySet, value: Any) -> None:
        """
        Append object PKs to the preload collection.

        Args:
            queryset: QuerySet to get model from
            value: Value(s) containing PKs to extract
        """
        if value == fields.empty:
            return

        query_hash = self.hash_from_queryset(queryset)
        self._ensure_preload_entry_exists(query_hash, queryset)

        values_list = value if isinstance(value, list) else [value]
        validated_pks = self._get_validated_pks(queryset.model, values_list)

        current_pks = set(self._objects_for_preload[query_hash]['pks'])
        new_pks = [pk for pk in validated_pks if pk not in current_pks]

        self._objects_for_preload[query_hash]['pks'].extend(new_pks)

    def _ensure_preload_entry_exists(self, query_hash: str, queryset: QuerySet) -> None:
        """Ensure preload entry exists for the given query hash."""
        if query_hash not in self._objects_for_preload:
            self._objects_for_preload[query_hash] = {'queryset': queryset, 'pks': []}

    @staticmethod
    def _get_validated_pks(model: Type[Model], values: List[Any]) -> List[Any]:
        """
        Extract and validate PKs from values.

        Args:
            model: Model class to get PK field from
            values: List of values to extract PKs from

        Returns:
            List of validated PK values
        """
        result = []
        pk_field = model._meta.pk

        for value in values:
            try:
                if isinstance(value, dict):
                    value = value.get(pk_field.name)
                if value is not None:
                    result.append(pk_field.get_prep_value(value))
            except (ValueError, TypeError):
                # Skip invalid PKs
                continue

        return result

    @staticmethod
    def find_preload_objects_manager(serializer: serializers.BaseSerializer) -> Optional['PreloadObjectsManager']:
        """
        Find PreloadObjectsManager in the serializer hierarchy.

        Args:
            serializer: Serializer to search from

        Returns:
            PreloadObjectsManager if found, None otherwise
        """
        manager = getattr(serializer, '_preload_objects_manager', None)
        if manager is not None:
            return manager

        parent = getattr(serializer, 'parent', None)
        if parent:
            return PreloadObjectsManager.find_preload_objects_manager(parent)

        return None

    @staticmethod
    def hash_from_queryset(queryset: QuerySet) -> str:
        """
        Generate hash from queryset for caching purposes.

        Args:
            queryset: QuerySet to generate hash from

        Returns:
            Hash string
        """
        if hasattr(queryset, 'query'):
            text = str(queryset.query)
        elif hasattr(queryset, 'objects'):
            text = str(queryset.objects)
        else:
            text = str(queryset)

        return blake2s(text.encode()).hexdigest()

    @staticmethod
    def enable_search_for_preloaded_objects() -> None:
        """
        Monkey patch PrimaryKeyRelatedField to use preloaded objects.
        This method modifies the behavior of to_internal_value to check preloaded objects first.
        """
        if hasattr(PrimaryKeyRelatedField, '_default_to_internal_value'):
            return

        # Store original method
        PrimaryKeyRelatedField._default_to_internal_value = PrimaryKeyRelatedField.to_internal_value

        def enhanced_to_internal_value(self: PrimaryKeyRelatedField, data: Any) -> Model:
            """Enhanced to_internal_value that uses preloaded objects when available."""
            query_hash = PreloadObjectsManager.hash_from_queryset(self.queryset)
            manager = PreloadObjectsManager.find_preload_objects_manager(self)

            if manager:
                # Ensure preloaded objects list exists
                if query_hash not in manager.preloaded_objects:
                    manager.preloaded_objects[query_hash] = []

                # Try to find object in preloaded objects
                preloaded_obj = PreloadObjectsManager._find_preloaded_object(
                    manager.preloaded_objects[query_hash], data
                )
                if preloaded_obj:
                    return preloaded_obj

            # Fall back to original method
            if hasattr(self, '_default_to_internal_value'):
                result = self._default_to_internal_value(data)

                # Cache the result for future use
                if manager:
                    PreloadObjectsManager._cache_loaded_object(manager, query_hash, result)

                return result

            # This should not happen, but just in case
            return super(PrimaryKeyRelatedField, self).to_internal_value(data)

        # Replace the method
        PrimaryKeyRelatedField.to_internal_value = enhanced_to_internal_value

    @staticmethod
    def _find_preloaded_object(objects: Union[List[Model], QuerySet], pk_value: Any) -> Optional[Model]:
        """Find object with matching PK in preloaded objects."""
        for obj in objects:
            if getattr(obj, 'pk') == pk_value:
                return obj
        return None

    @staticmethod
    def _cache_loaded_object(manager: 'PreloadObjectsManager', query_hash: str, obj: Model) -> None:
        """Cache a newly loaded object in the preloaded objects."""
        preloaded_objects = manager.preloaded_objects[query_hash]

        # Convert QuerySet to list if needed
        if isinstance(preloaded_objects, QuerySet):
            preloaded_objects = list(preloaded_objects)
            manager.preloaded_objects[query_hash] = preloaded_objects

        preloaded_objects.append(obj)

    @staticmethod
    def disable_search_for_preloaded_objects() -> None:
        """
        Restore original PrimaryKeyRelatedField behavior.
        Removes the monkey patch applied by enable_search_for_preloaded_objects.
        """
        if hasattr(PrimaryKeyRelatedField, '_default_to_internal_value'):
            PrimaryKeyRelatedField.to_internal_value = PrimaryKeyRelatedField._default_to_internal_value
            delattr(PrimaryKeyRelatedField, '_default_to_internal_value')
