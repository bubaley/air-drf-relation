from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.utils import model_meta
from rest_framework import serializers
from django.db.models import ForeignKey

from air_drf_relation.fields import RelatedField


class AirModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        self.extra_kwargs = self._get_extra_kwargs(extra_kwargs=kwargs.pop('extra_kwargs', {}))
        self.related_fields = self._get_related_fields()
        self._update_extra_kwargs_in_fields()
        super(AirModelSerializer, self).__init__(*args, **kwargs)
        self._update_related_fields()
        self._filter_queryset_by_fields()

    class Meta:
        model = None
        fields = ()
        read_only_fields = ()
        write_only_fields = ()
        extra_kwargs = {}

    def _update_related_fields(self):
        info = model_meta.get_field_info(self.Meta.model)
        for field_name, field in self.related_fields.items():
            # field.parent = self
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
        for field_name, field in self.related_fields.items():
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
        if not hasattr(self.Meta, 'extra_kwargs'):
            return extra_kwargs

        if not len(extra_kwargs):
            return self.Meta.extra_kwargs

        meta_extra_kwargs = self.Meta.extra_kwargs
        for key, value in extra_kwargs.items():
            current_meta_kwargs = meta_extra_kwargs.get(key)
            if current_meta_kwargs:
                extra_kwargs[key] = {**current_meta_kwargs, **value}
            else:
                extra_kwargs[key] = value

    def _update_extra_kwargs_in_fields(self):
        for key, value in self.extra_kwargs.items():
            try:
                self.fields.fields[key].__dict__.update(value)
                self.fields.fields[key]._kwargs = {**self.fields.fields[key]._kwargs, **value}
            except KeyError:
                continue
