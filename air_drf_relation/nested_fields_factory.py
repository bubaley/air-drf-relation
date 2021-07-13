from uuid import UUID

from rest_framework.exceptions import ValidationError


class NestedSaveField:
    def __init__(self, field_name, update_objects=True, **kwargs):
        self.field_name = field_name
        self.model = None
        self.pk = None
        self.reverse_field_name = None
        self.update_objects = update_objects
        self.validated_data = list()
        self.initial_data = list()
        self.objects = list()
        self._kwargs = kwargs

    def set_data(self, validated_data: list, initial_data: list):
        self.validated_data = validated_data
        self.initial_data = initial_data

    def set_params(self, reverse_field_name, model):
        self.reverse_field_name = reverse_field_name
        self.model = model
        self.pk = model._meta.pk.name


class NestedSaveFactory:
    def __init__(self, serializer, nested_save_fields):
        self.serializer = serializer
        self.validated_data = None
        self.instance = None
        self.initial_data = None
        self.initial_nested_fields = nested_save_fields
        self.nested_fields: list[NestedSaveField] = list()
        self.model = serializer.Meta.model
        self._set_nested_fields()
        self.created = None

    def set_data(self, validated_data, instance=None):
        self.validated_data = validated_data
        self.instance = instance
        self.initial_data = self.serializer.initial_data
        for nested_field in self.nested_fields:
            validated_data = self.validated_data.pop(nested_field.field_name, list())
            initial_data = self.initial_data.pop(nested_field.field_name, list())
            nested_field.set_data(validated_data=validated_data, initial_data=initial_data)
        return self

    def save_instance(self):
        if self.instance:
            self.instance.__dict__.update(self.validated_data)
            self.instance.save()
            self.created = False
        else:
            self.instance = self.model.objects.create(**self.validated_data)
            self.created = True
        return self

    def save_nested_fields(self):
        if not self.instance:
            raise ValidationError({
                'instance': ['Cannot save nested fields without instance']
            })
        for nested_field in self.nested_fields:
            if not nested_field.update_objects:
                self._save_nested_objects_without_update(nested_field=nested_field)
            else:
                self._save_nested_objects_with_update(nested_field=nested_field)

        return self

    def _save_nested_objects_with_update(self, nested_field):
        saved_pks = list()
        field = getattr(self.instance, nested_field.field_name)
        _current_pks = field.all().values_list(nested_field.pk, flat=True)
        current_pks = list()
        for el in _current_pks:
            if type(el) == UUID:
                current_pks.append(str(el))
                continue
            current_pks.append(el)
        for index, value in enumerate(nested_field.validated_data):
            current_pk = nested_field.initial_data[index].get(nested_field.pk)
            if current_pk and current_pk not in current_pks:
                continue
            current_object = None
            if current_pk:
                current_object = field.filter(pk=current_pk).first()
                current_object.__dict__.update(**value)
            if not current_object:
                current_object = nested_field.model(**value, **{nested_field.reverse_field_name: self.instance})
            current_object.save()
            saved_pks.append(current_object.pk)
        field.exclude(pk__in=saved_pks).delete()

    def _save_nested_objects_without_update(self, nested_field: NestedSaveField):
        getattr(self.instance, nested_field.field_name).all().delete()
        for value in nested_field.validated_data:
            obj = nested_field.model.objects.create(**value, **{nested_field.reverse_field_name: self.instance})
            nested_field.objects.append(obj)

    def _set_nested_fields(self):
        if type(self.initial_nested_fields) == dict:
            for field_name, value in self.initial_nested_fields.items():
                self.nested_fields.append(NestedSaveField(field_name=field_name, **value))
        elif type(self.initial_nested_fields) in (list, tuple):
            for field_name in self.initial_nested_fields:
                self.nested_fields.append(NestedSaveField(field_name=field_name))
        self._set_nested_fields_params()

    def _set_nested_fields_params(self):
        for el in self.nested_fields:
            field = getattr(self.model, el.field_name).field
            el.set_params(reverse_field_name=field.name, model=field.model)
