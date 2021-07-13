from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.utils import model_meta
from rest_framework import serializers
from django.db.models import ForeignKey

from air_drf_relation.context_builder import set_empty_request_in_kwargs
from air_drf_relation.extra_kwargs import ExtraKwargsFactory
from air_drf_relation.fields import AirRelatedField
from air_drf_relation.nested_fields_factory import NestedSaveFactory
from rest_framework.validators import UniqueValidator


class AirModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = ()
        read_only_fields = ()
        write_only_fields = ()
        extra_kwargs = {}

    def __init__(self, *args, **kwargs):
        self.action = kwargs.pop('action', None)
        self.user = kwargs.pop('user', None)
        self.nested_save_fields = self._get_nested_save_fields()
        self.nested_save_factory: NestedSaveFactory = None
        if 'context' not in kwargs:
            set_empty_request_in_kwargs(kwargs=kwargs)
        if not self.action:
            self._set_action_from_view(kwargs=kwargs)
        if not self.user:
            self._set_user_from_request(kwargs)
        self.extra_kwargs = self._get_extra_kwargs(kwargs)
        self._update_extra_kwargs_in_fields()
        super(AirModelSerializer, self).__init__(*args, **kwargs)
        self._set_nested_save_factory()
        self._update_fields()

    def create(self, validated_data):
        if self.nested_save_factory:
            return self.create_with_nested_fields(validated_data=validated_data)
        else:
            return super(AirModelSerializer, self).create(validated_data=validated_data)

    def update(self, instance, validated_data):
        if self.nested_save_factory:
            return self.update_with_nested_fields(validated_data=validated_data, instance=instance)
        else:
            return super(AirModelSerializer, self).update(instance=instance, validated_data=validated_data)

    def is_valid(self, raise_exception=False):
        if self.nested_save_factory:
            for el in self.nested_save_factory.nested_fields:
                field = self.fields.fields[el.field_name].child.fields.fields[el.reverse_field_name]
                pk_field = self.fields.fields[el.field_name].child.fields.fields[el.pk]
                pk_fields_validators = pk_field.validators
                unique_validator = next((val for val in pk_fields_validators if type(val) == UniqueValidator), None)
                if unique_validator:
                    pk_fields_validators.remove(unique_validator)
                setattr(field, 'read_only', True)
        self._filter_queryset_by_fields()
        super(AirModelSerializer, self).is_valid(raise_exception=raise_exception)

    def _update_fields(self):
        info = model_meta.get_field_info(self.Meta.model)
        hidden_fields = [field_name for field_name, field in self.fields.items() if
                         hasattr(field, 'hidden') and getattr(field, 'hidden', True)]
        for el in hidden_fields:
            del self.fields[el]
        for field_name, field in self.fields.items():
            if not isinstance(field, AirRelatedField):
                continue
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
                function_name = f'queryset_{field.source}'
            if hasattr(self.__class__, function_name) and callable(getattr(self.__class__, function_name)):
                field.queryset = getattr(self.__class__, function_name)(self=self, queryset=field.queryset)

    def _get_related_fields(self):
        related_fields = dict()
        for field_name, field in self.fields.items():
            if type(field) in (AirRelatedField, PrimaryKeyRelatedField):
                related_fields[field_name] = field
        return related_fields

    def _get_extra_kwargs(self, kwargs: dict):
        data = {'extra_kwargs': kwargs.pop('extra_kwargs', {})}
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

    def _get_nested_save_fields(self):
        return getattr(self.Meta, 'nested_save_fields') if hasattr(self.Meta, 'nested_save_fields') else None

    def _set_nested_save_factory(self):
        self.nested_save_factory = NestedSaveFactory(serializer=self, nested_save_fields=self.nested_save_fields)

    def create_with_nested_fields(self, validated_data):
        self.nested_save_factory.set_data(validated_data=validated_data)
        instance = super(AirModelSerializer, self).create(validated_data=validated_data)
        self.nested_save_factory.instance = instance
        self.nested_save_factory.created = True
        self.nested_save_factory.save_nested_fields()
        return instance

    def update_with_nested_fields(self, instance, validated_data):
        self.nested_save_factory.set_data(instance=instance, validated_data=validated_data)
        instance = super(AirModelSerializer, self).update(instance=instance, validated_data=validated_data)
        self.nested_save_factory.instance = instance
        self.nested_save_factory.created = False
        self.nested_save_factory.save_nested_fields()
        return instance

    def __new__(cls, *args, **kwargs):
        if kwargs.pop('many', False):
            if 'context' not in kwargs:
                set_empty_request_in_kwargs(kwargs=kwargs)
            return cls.many_init(*args, **kwargs)
        return super().__new__(cls, *args, **kwargs)
