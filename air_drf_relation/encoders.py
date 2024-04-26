import json

from air_drf_relation.model_fields import AirDataclassField
from django.core.serializers.json import Serializer as DjangoSerializer, Deserializer, DjangoJSONEncoder


class Serializer(DjangoSerializer):
    def get_dump_object(self, obj):
        data = {'model': str(obj._meta)}
        if not self.use_natural_primary_keys or not hasattr(obj, 'natural_key'):
            data['pk'] = self._value_from_field(obj, obj._meta.pk)

        for index, field in enumerate(obj._meta.fields):
            if isinstance(field, AirDataclassField):
                self._current[field.name] = json.dumps(self._current[field.name].default_dict())

        data['fields'] = self._current
        return data
