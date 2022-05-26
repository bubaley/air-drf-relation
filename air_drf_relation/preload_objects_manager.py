from django.db.models import QuerySet
from rest_framework import serializers, fields
from hashlib import md5
from rest_framework.relations import PrimaryKeyRelatedField

from air_drf_relation import air_drf_relation_settings


class PreloadObjectsManager:
    def __init__(self, serializer):
        self.preloaded_objects = {}
        self._objects_for_preload = {}
        self._serializer = serializer.child if issubclass(serializer.__class__,
                                                          serializers.ListSerializer) else serializer

    @staticmethod
    def get_preload_objects_manager(serializer):
        manager = PreloadObjectsManager.find_preload_objects_manager(serializer)
        return manager if manager else PreloadObjectsManager(serializer)

    def init(self):
        if not air_drf_relation_settings.get('USE_PRELOAD'):
            return None
        self._init(self._serializer, self._serializer.initial_data)
        for query_hash, data in self._objects_for_preload.items():
            self.preloaded_objects[query_hash] = data['queryset'].filter(pk__in=list(set(data['pks']))) if data[
                'pks'] else []
        return self

    def _init(self, serializer, data):
        if not data:
            return
        _data = data if type(data) == list else [data]
        current_fields = list(serializer._writable_fields)
        for value in _data:
            for field in current_fields:
                field_type = type(field)
                if issubclass(field_type, serializers.PrimaryKeyRelatedField):
                    val = field.get_value(value)
                    self._append_object_pks(field.queryset, val)
                elif issubclass(field_type, serializers.ManyRelatedField):
                    val = field.get_value(value)
                    self._append_object_pks(field.child_relation.queryset, val)
                elif issubclass(field_type, serializers.Serializer):
                    self._init(field, value.get(field.field_name, None))
                elif issubclass(field_type, serializers.ListSerializer) and hasattr(field, 'child'):
                    self._init(field.child, value.get(field.field_name, None))
        return self

    def _append_object_pks(self, queryset, value):
        query_hash = self.hash_from_queryset(queryset)
        if value == fields.empty:
            return
        if query_hash not in self._objects_for_preload:
            self._objects_for_preload[query_hash] = {
                'queryset': queryset,
                'pks': []
            }
        _values = value if type(value) == list else [value]
        current_objects = self._objects_for_preload[query_hash]['pks']
        data = self._objects_for_preload[query_hash]
        data['pks'] += [v for v in self._get_validated_pks(queryset.model, _values) if v not in current_objects]

    @staticmethod
    def _get_validated_pks(model, values):
        result = []
        for v in values:
            try:
                if type(v) == dict:
                    v = v.get(model._meta.pk.name)
                result.append(model._meta.pk.get_prep_value(v))
            except (ValueError, TypeError):
                continue
        return result

    @staticmethod
    def find_preload_objects_manager(serializer):
        preloaded_objects_attr = getattr(serializer, '_preload_objects_manager', None)
        if preloaded_objects_attr is not None:
            return preloaded_objects_attr
        parent = getattr(serializer, 'parent', None)
        if not parent:
            return None
        return PreloadObjectsManager.find_preload_objects_manager(parent)

    @staticmethod
    def hash_from_queryset(queryset):
        if hasattr(queryset, 'query'):
            text = str(queryset.query)
        elif hasattr(queryset, 'objects'):
            text = str(queryset.objects)
        else:
            text = str(queryset)
        return md5(text.encode()).hexdigest()

    @staticmethod
    def enable_search_for_preloaded_objects():
        if hasattr(PrimaryKeyRelatedField, '_default_to_internal_value'):
            return
        PrimaryKeyRelatedField._default_to_internal_value = PrimaryKeyRelatedField.to_internal_value

        def to_internal_value(self: PrimaryKeyRelatedField, data):
            query_hash = PreloadObjectsManager.hash_from_queryset(self.queryset)
            manager = PreloadObjectsManager.find_preload_objects_manager(self)
            if manager:
                if not manager.preloaded_objects.get(query_hash):
                    manager.preloaded_objects[query_hash] = []
                objects_by_queryset = manager.preloaded_objects[query_hash]
                current_value = next((v for v in objects_by_queryset if getattr(v, 'pk') == data), None)
                if current_value:
                    return current_value
            if hasattr(self, '_default_to_internal_value'):
                result = self._default_to_internal_value(data)
                if manager:
                    if type(manager.preloaded_objects[query_hash]) == QuerySet:
                        manager.preloaded_objects[query_hash] = list(manager.preloaded_objects[query_hash])
                    manager.preloaded_objects[query_hash].append(result)
                return result

        PrimaryKeyRelatedField.to_internal_value = to_internal_value

    @staticmethod
    def disable_search_for_preloaded_objects():
        if hasattr(PrimaryKeyRelatedField, '_default_to_internal_value'):
            PrimaryKeyRelatedField.to_internal_value = PrimaryKeyRelatedField._default_to_internal_value
            delattr(PrimaryKeyRelatedField, '_default_to_internal_value')
