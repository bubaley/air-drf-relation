from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.permissions import SAFE_METHODS


def get_related_object(search, model, fail_on_null=True, create_on_null=False, fail_on_not_found=True,
                       extra_filter=None):
    """
    Find an instance by primary key which might be an integer, string, dict with "id" key or list of keys
    :param search:
    :param model:
    :param fail_on_null: Raise exception if value in request data is null.
    :param create_on_null: Try to create a new instance if not found.
    :param fail_on_not_found: Raise exception if instance not found. (doesn't work on list of primary keys)
    :param extra_filter: Extra params to filter
    :return:
    """
    if extra_filter is None:
        extra_filter = {}

    if isinstance(search, int):
        pk = search
    elif isinstance(search, str):
        try:
            pk = int(search)
        except Exception:
            if fail_on_null:
                raise ValidationError(f'Incorrect {model.__name__} field.')
            else:
                return None
    elif isinstance(search, dict) and search.get('id'):
        pk = search.get('id')
    elif isinstance(search, dict) and create_on_null:
        return model.objects.create(**search)
    elif isinstance(search, list) or isinstance(search, tuple):
        pks = list()
        for item in search:  # flat list to list of ids
            if isinstance(item, dict) and item.get('id'):
                pks.append(item.get('id'))
            elif isinstance(item, int):
                pks.append(item)
            elif isinstance(item, str):
                pks.append(int(item))
            else:
                raise ValidationError(f'Primary key "{item}" is incorrect')
        return model.objects.filter(pk__in=pks, **extra_filter)
    elif fail_on_null:
        raise ValidationError(f'Incorrect {model.__name__} field.')
    else:
        return None

    obj = model.objects.filter(pk=pk, **extra_filter).first()
    if not obj and fail_on_not_found:
        raise NotFound(f'{model.__name__} not found.')

    return obj


def get_relation_from_request(request, key: str, data: dict, model, fail_on_empty=False, fail_on_null=True,
                              fail_on_not_found=True, create_on_null=False, types=None, extra_filter=None):
    """
    Get primary key from request, find instance and put it to data.
    :param extra_filter:
    :param request:
    :param key:
    :param data: Dictionary to put instance.
    :param model: Model of instance.
    :param fail_on_empty: Raise exception if key is missed in request data.
    :param fail_on_null: Raise exception if value in request data is null.
    :param fail_on_not_found: Raise exception if instance not found. (doesn't work on list of primary keys)
    :param create_on_null: Try to create a new instance if not found.
    :param types: Available types of value in request data.
    """
    if extra_filter is None:
        extra_filter = {}
    if types is None:
        types = []
    request_data = request.query_params if request.method in SAFE_METHODS else request.data
    if key in request_data.keys():
        obj = request_data.get(key)
        if len(types) > 0:
            correct_type = False
            for _type in types:
                if isinstance(obj, _type):
                    correct_type = True
                    break
            if not correct_type:
                raise ValidationError(f'Incorrect type of field \'{key}\'.')

        obj = get_related_object(obj, model, fail_on_null=fail_on_null, create_on_null=create_on_null,
                                 fail_on_not_found=fail_on_not_found, extra_filter=extra_filter)
        data.update({key: obj})
        return obj
    elif fail_on_empty:
        raise ValidationError(f'Missing field \'{key}\'')


class RelatedField(PrimaryKeyRelatedField):

    def __init__(self, **kwargs):
        self.serializer = kwargs.pop('serializer')
        self.extra_filter = kwargs.pop('extra_filter', None)
        self.fail_on_null = kwargs.pop('fail_on_null', True)
        self.fail_on_not_found = kwargs.pop('fail_on_not_found', True)
        self.queryset = kwargs.pop('queryset', None)
        if not self.queryset and self.serializer:
            self.queryset = self.serializer.Meta.model.objects
        super().__init__(**kwargs)

    def use_pk_only_optimization(self):
        return False

    def to_internal_value(self, data):
        return get_related_object(data, self.queryset.model, fail_on_not_found=self.fail_on_not_found, extra_filter=self.extra_filter)

    def to_representation(self, value):
        if self.serializer:
            return self.serializer(value).data
        return value.pk
