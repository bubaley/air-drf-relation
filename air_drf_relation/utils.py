def get_pk_from_data(data, pk_name):
    pk = None
    if type(data) in [int, str]:
        pk = data
    elif type(data) == dict:
        pk = data.get(pk_name)
    if not pk:
        raise TypeError
    return pk


def get_related_object(data, queryset):
    pk_name = queryset.model._meta.pk.name
    if type(data) not in [list, tuple]:
        pk = get_pk_from_data(data, pk_name)
        return queryset.get(pk=pk)
    else:
        pks = list()
        for item in data:
            pks.append(get_pk_from_data(item, pk_name))
        return queryset.filter(pk__in=pks)


def create_dict_from_list(values: list, value_data) -> dict:
    result = dict()
    for el in values:
        result[el] = value_data
    return result
