import uuid


def get_pk_from_data(data, pk_name):
    if type(data) in [list, tuple]:
        return [v.get(pk_name) if type(v) == dict else v for v in data]
    return data.get(pk_name) if type(data) == dict else data


def create_dict_from_list(values: list, value_data) -> dict:
    result = {}
    for el in values:
        result[el] = value_data
    return result


def stringify_uuids(value):
    if isinstance(value, dict):
        for k in value.keys():
            value[k] = stringify_uuids(value[k])
    elif isinstance(value, list) and not isinstance(value, str):
        for i, v in enumerate(value):
            value[i] = stringify_uuids(v)
    elif isinstance(value, uuid.UUID):
        return str(value)
    return value


def is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False
