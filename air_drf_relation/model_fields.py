from dacite import from_dict
from django.db import models
from dataclasses import asdict, is_dataclass
import json


class AirDataclassField(models.JSONField):

    def __init__(self, data_class, *args, **kwargs):
        self.data_class = data_class
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['data_class'] = self.data_class
        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        obj = json.loads(value)
        if obj == self._get_default():
            return obj
        return from_dict(data_class=self.data_class, data=obj)

    def to_python(self, value):
        if isinstance(value, self.data_class):
            return value
        if value is None:
            return value
        obj = json.loads(value)
        return from_dict(data_class=self.data_class, data=obj)

    def get_prep_value(self, value):
        if not is_dataclass(value):
            return json.dumps(self._get_default())
        return json.dumps(asdict(value))
