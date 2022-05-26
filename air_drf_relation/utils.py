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


def set_values_to_class(instance, values: dict):
    for key, value in values.items():
        setattr(instance, key, value)
    return instance


def is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False
