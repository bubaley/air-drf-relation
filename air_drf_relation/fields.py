from django.core.exceptions import ObjectDoesNotExist
from rest_framework.relations import PrimaryKeyRelatedField

from air_drf_relation.utils import get_related_object


class AirRelatedField(PrimaryKeyRelatedField):
    def __init__(self, serializer, **kwargs):
        self.serializer = serializer
        self.pk_only = kwargs.pop('pk_only', False)
        self.hidden = kwargs.pop('hidden', False)
        self.queryset_function_name = kwargs.pop('queryset_function_name', None)
        self.queryset_function_disabled = kwargs.pop('queryset_function_disabled', False)

        if not kwargs.get('read_only'):
            self.queryset = kwargs.pop('queryset', None)
            if not self.queryset:
                self.queryset = self.serializer.Meta.model.objects
        else:
            self.queryset_function_disabled = True

        super().__init__(**kwargs)

    def __call__(self, *args, **kwargs):
        super.__call__(*args, **kwargs)

    def use_pk_only_optimization(self):
        return self.pk_only

    def to_internal_value(self, data):
        try:
            return get_related_object(data, queryset=self.queryset)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)

    def to_representation(self, value):
        if not self.pk_only:
            return self.serializer(value, context=self.context).data
        return value.pk
