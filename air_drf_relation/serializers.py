from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.utils import model_meta
from rest_framework import serializers
from django.db.models import ForeignKey
from copy import deepcopy

from air_drf_relation.fields import RelatedField


class AirModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        self.action = kwargs.pop('action', None)
        if not self.action:
            self._set_action_from_view(kwargs=kwargs)
        self.extra_kwargs = self._get_extra_kwargs(extra_kwargs=kwargs.pop('extra_kwargs', {}))
        self._update_extra_kwargs_in_fields()

        super(AirModelSerializer, self).__init__(*args, **kwargs)
        self._update_fields()

    def is_valid(self, raise_exception=False):
        self._filter_queryset_by_fields()
        super(AirModelSerializer, self).is_valid(raise_exception=raise_exception)

    class Meta:
        model = None
        fields = ()
        read_only_fields = ()
        write_only_fields = ()
        extra_kwargs = {}

    def _update_fields(self):
        info = model_meta.get_field_info(self.Meta.model)
        hidden_fields = [field_name for field_name, field in self.fields.items() if
                         hasattr(field, 'hidden') and getattr(field, 'hidden', True)]
        for el in hidden_fields:
            del self.fields[el]
        for field_name, field in self.fields.items():
            if not isinstance(field, RelatedField):
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
            function_name = None
            if isinstance(field, RelatedField):
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
            if type(field) in (RelatedField, PrimaryKeyRelatedField):
                related_fields[field_name] = field
        return related_fields

    def _get_extra_kwargs(self, extra_kwargs: dict):
        meta_extra_kwargs = deepcopy(self.Meta.extra_kwargs) if hasattr(self.Meta, 'extra_kwargs') else {}
        self._delete_custom_extra_kwargs_in_meta()
        action_extra_kwargs = {}
        if hasattr(self.Meta, 'action_extra_kwargs') and self.action:
            _action_extra_kwargs = deepcopy(self.Meta.action_extra_kwargs)
            _current_actions = {}
            for key, value in _action_extra_kwargs.items():
                keys = key.replace(' ', '').split(',')
                for current_key in keys:
                    _current_actions[current_key] = value
            action_extra_kwargs = _current_actions.get(self.action)
            if not action_extra_kwargs:
                action_extra_kwargs = _current_actions.get('_', {})

        unique_field_names = list(extra_kwargs.keys()) + list(meta_extra_kwargs.keys()) + list(
            action_extra_kwargs.keys())
        unique_field_names = list(set(unique_field_names))
        result_kwargs = {}
        for name in unique_field_names:
            result_kwargs[name] = {**meta_extra_kwargs.get(name, {}), **action_extra_kwargs.get(name, {}),
                                   **extra_kwargs.get(name, {})}
        return result_kwargs

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
        view = kwargs.get('context', {}).get('view')
        if view:
            self.action = view.action
