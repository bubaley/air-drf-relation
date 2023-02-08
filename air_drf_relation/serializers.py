from typing import TypeVar, Dict, Any
from uuid import UUID
from dataclasses import is_dataclass
from rest_framework.fields import empty
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.utils import model_meta
from rest_framework import serializers
from django.db.models import ForeignKey
from rest_framework_dataclasses.serializers import DataclassSerializer
from rest_framework_dataclasses.types import Dataclass

from air_drf_relation.context_builder import set_empty_request_in_kwargs
from air_drf_relation.extra_kwargs import ExtraKwargsFactory
from air_drf_relation.fields import AirRelatedField
from air_drf_relation.preload_objects_manager import PreloadObjectsManager
from air_drf_relation.queryset_optimization import optimize_queryset

T = TypeVar('T', bound=Dataclass)


class AirModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = ()
        read_only_fields = ()
        write_only_fields = ()
        extra_kwargs = {}
        optimize_queryset = True

    def __init__(self, *args, **kwargs):
        self.action = kwargs.pop('action', None)
        self.user = kwargs.pop('user', None)
        self._preload_objects_manager = None
        self.optimize_queryset = True
        if 'optimize_queryset' in kwargs:
            self.optimize_queryset = kwargs.pop('optimize_queryset', True)
        elif hasattr(self.Meta, 'optimize_queryset'):
            self.optimize_queryset = getattr(self.Meta, 'optimize_queryset', True)
        self._initial_extra_kwargs = kwargs.pop('extra_kwargs', {})
        if 'context' not in kwargs:
            set_empty_request_in_kwargs(kwargs=kwargs)

        if not self.action:
            self._set_action_from_view(kwargs=kwargs)
        if not self.user:
            self._set_user_from_request(kwargs)
        self.extra_kwargs = self._get_extra_kwargs()
        self._update_extra_kwargs_in_fields()
        super(AirModelSerializer, self).__init__(*args, **kwargs)
        self._update_fields()

    def update_or_create(self, instance, validated_data):
        super_class = super(AirModelSerializer, self)
        return super_class.create(validated_data) if not instance else super_class.update(instance, validated_data)

    def create(self, validated_data):
        return self.update_or_create(None, validated_data)

    def update(self, instance, validated_data):
        return self.update_or_create(instance, validated_data)

    def is_valid(self, raise_exception=False):
        self._filter_queryset_by_fields()
        self._preload_objects_manager = PreloadObjectsManager.get_preload_objects_manager(self).init()
        super(AirModelSerializer, self).is_valid(raise_exception=raise_exception)

    def _update_fields(self):
        if not hasattr(self.Meta, 'model'):
            return
        info = model_meta.get_field_info(self.Meta.model)
        hidden_fields = [field_name for field_name, field in self.fields.items() if
                         hasattr(field, 'hidden') and getattr(field, 'hidden', True)]
        for el in hidden_fields:
            del self.fields[el]
        for field_name, field in self.fields.items():
            if not isinstance(field, AirRelatedField):
                continue
            field.parent = self
            model_field: ForeignKey = info.relations[field_name].model_field
            field_kwargs = field._kwargs
            if not model_field.editable:
                field.read_only = True
                continue
            if model_field.null:
                if field_kwargs.get('required') is None:
                    field.required = False
                if field_kwargs.get('allow_null') is None:
                    field.allow_null = True

    def _filter_queryset_by_fields(self):
        related_fields = self._get_related_fields()
        for field_name, field in related_fields.items():
            if not self.initial_data.get(field_name):
                continue
            function_name = None
            if isinstance(field, AirRelatedField):
                if field.queryset_function_disabled:
                    return
                function_name = field.queryset_function_name
            if not function_name:
                function_name = f'queryset_{field.field_name}'
            if hasattr(self.__class__, function_name) and callable(getattr(self.__class__, function_name)):
                field.queryset = getattr(self.__class__, function_name)(self=self, queryset=field.queryset)

    def _get_related_fields(self):
        related_fields = dict()
        for field_name, field in self.fields.items():
            if type(field) in (AirRelatedField, PrimaryKeyRelatedField):
                related_fields[field_name] = field
        return related_fields

    def _get_extra_kwargs(self):
        data = {'extra_kwargs': self._initial_extra_kwargs}
        extra_kwargs = ExtraKwargsFactory(meta=self.Meta, data=data, action=self.action).init().extra_kwargs
        self._delete_custom_extra_kwargs_in_meta()
        return extra_kwargs

    def _update_extra_kwargs_in_fields(self):
        for key, value in self.extra_kwargs.items():
            try:
                self.fields.fields[key].__dict__.update(value)
                self.fields.fields[key]._kwargs = {**self.fields.fields[key]._kwargs, **value}
            except KeyError:
                continue

    def _delete_custom_extra_kwargs_in_meta(self):
        if not hasattr(self.Meta, 'extra_kwargs'):
            return
        for field_name, field in self.Meta.extra_kwargs.items():
            field.pop('pk_only', None)
            field.pop('hidden', None)

    def _set_action_from_view(self, kwargs):
        context = kwargs.get('context', None)
        if not context:
            return
        view = context.get('view')
        if view:
            self.action = view.action

    def _set_user_from_request(self, kwargs):
        context = kwargs.get('context', None)
        if not context:
            return
        request = context.get('request')
        if request and hasattr(request, 'user'):
            user = getattr(request, 'user')
            if user.is_authenticated:
                self.user = user

    def __new__(cls, *args, **kwargs):
        if kwargs.pop('many', False):
            if 'context' not in kwargs:
                set_empty_request_in_kwargs(kwargs=kwargs)
            return cls.many_init(*args, **kwargs)
        return super().__new__(cls, *args, **kwargs)

    @classmethod
    def many_init(cls, *args, **kwargs):
        meta = getattr(cls, 'Meta', None)
        if not hasattr(meta, 'list_serializer_class'):
            setattr(meta, 'list_serializer_class', AirListSerializer)
        serializer = super(AirModelSerializer, cls).many_init(*args, **kwargs)

        if hasattr(serializer, 'parent') and serializer.parent is None:
            if serializer.child and \
                    hasattr(serializer.child, 'optimize_queryset') and serializer.child.optimize_queryset:
                serializer.instance = optimize_queryset(serializer.instance, serializer.child)
        return serializer

    def to_representation(self, instance):
        if getattr(self, 'parent') is None and self.optimize_queryset:
            instance = optimize_queryset(instance, self)
        data = super(AirModelSerializer, self).to_representation(instance)
        for el in data:
            if type(data[el]) == UUID:
                data[el] = str(data[el])
        return data


class AirListSerializer(serializers.ListSerializer):
    def __init__(self, *args, **list_kwargs):
        super(AirListSerializer, self).__init__(*args, **list_kwargs)
        self._preload_objects_manager = None

    def is_valid(self, raise_exception=False):
        self._preload_objects_manager = PreloadObjectsManager.get_preload_objects_manager(self).init()
        super(AirListSerializer, self).is_valid(raise_exception=raise_exception)

    def update(self, instance, validated_data):
        super(AirListSerializer, self).update(instance, validated_data)


class AirEmptySerializer(serializers.Serializer):

    def __init__(self, *args, **kwargs):
        super(AirEmptySerializer, self).__init__(*args, **kwargs)

    def update(self, instance, validated_data):
        raise NotImplemented()

    def create(self, validated_data):
        raise NotImplemented()


class AirDynamicSerializer(AirEmptySerializer):
    def __init__(self, *args, **kwargs):
        values = kwargs.pop('values')
        if not type(values) == dict:
            raise TypeError('values should be dict.')
        for key, value in values.items():
            self.fields.fields[key] = value
            self.fields.fields[key].field_name = key
            self.fields.fields[key].source_attrs = [key]
        super(AirDynamicSerializer, self).__init__(*args, **kwargs)


class AirDataclassSerializer(DataclassSerializer):
    def to_internal_value(self, data: Dict[str, Any]) -> T:
        instance = super(AirDataclassSerializer, self).to_internal_value(data)
        dataclass = self.Meta.dataclass
        for key in instance.__dict__.keys():
            if getattr(instance, key) == empty:
                if self.instance:
                    value = getattr(self.instance, key, None)
                else:
                    value = getattr(dataclass, key, None)
                setattr(instance, key, value)
        return instance

    def run_validation(self, data=empty):
        if self.parent and getattr(self.parent, 'instance', None):
            self.instance = getattr(self.parent.instance, self.source, None)
        return super(AirDataclassSerializer, self).run_validation(data)

    def to_representation(self, instance):
        if instance is not None:
            if isinstance(instance, dict):
                for el in self._writable_fields:
                    if el.field_name not in instance:
                        instance[el.field_name] = None
        return super(AirDataclassSerializer, self).to_representation(instance)
