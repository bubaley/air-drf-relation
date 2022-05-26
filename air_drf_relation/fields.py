from rest_framework.relations import PrimaryKeyRelatedField, Field
from air_drf_relation.utils import get_pk_from_data


class AirRelatedField(PrimaryKeyRelatedField):
    def __init__(self, serializer, **kwargs):
        self.serializer = serializer
        self.pk_only = kwargs.pop('pk_only', False)
        self.hidden = kwargs.pop('hidden', False)
        self.queryset_function_name = kwargs.pop('queryset_function_name', None)
        self.queryset_function_disabled = kwargs.pop('queryset_function_disabled', False)
        self.parent = None
        kwargs.pop('as_serializer', None)

        if not kwargs.get('read_only'):
            self.queryset = kwargs.pop('queryset', None)
            if not self.queryset:
                self.queryset = self.serializer.Meta.model.objects
        else:
            self.queryset_function_disabled = True

        super().__init__(**kwargs)
        self.parent = None

    def __new__(cls, serializer, *args, **kwargs):
        if kwargs.pop('as_serializer', False):
            return serializer(*args, **kwargs)
        return super().__new__(cls, serializer, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        super.__call__(*args, **kwargs)

    def use_pk_only_optimization(self):
        return self.pk_only

    def to_internal_value(self, data):
        data = get_pk_from_data(data, self.queryset.model._meta.pk.name)
        return super(AirRelatedField, self).to_internal_value(data)

    def to_representation(self, value):
        if not self.pk_only:
            serializer = self.serializer(value, context=self.context)
            serializer.parent = self.parent
            return serializer.data
        return value.pk


class AirAnyField(Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        return data
