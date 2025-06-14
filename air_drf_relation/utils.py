import uuid
from typing import Any, Dict, List, Tuple, Union


def get_pk_from_data(data: Union[Dict[str, Any], List[Any], Tuple[Any, ...], Any], pk_name: str) -> Any:
    """
    Extract primary key value(s) from data structure.

    Handles various data formats:
    - Dict: Extracts value by pk_name key
    - List/Tuple: Recursively extracts pk from each item
    - Other: Returns as-is

    Args:
        data: Data structure to extract PK from
        pk_name: Name of the primary key field

    Returns:
        Primary key value(s) or original data
    """
    if isinstance(data, (list, tuple)):
        return [_extract_pk_from_item(item, pk_name) for item in data]

    return _extract_pk_from_item(data, pk_name)


def _extract_pk_from_item(item: Any, pk_name: str) -> Any:
    """
    Extract primary key from a single item.

    Args:
        item: Item to extract PK from
        pk_name: Name of the primary key field

    Returns:
        Primary key value or original item
    """
    if isinstance(item, dict):
        return item.get(pk_name)
    return item


def create_dict_from_list(values: List[str], value_data: Any) -> Dict[str, Any]:
    """
    Create dictionary from list of keys with the same value for each key.

    Args:
        values: List of keys for the dictionary
        value_data: Value to assign to each key

    Returns:
        Dictionary with keys from values and value_data as values

    Example:
        >>> create_dict_from_list(['a', 'b', 'c'], {'hidden': True})
        {'a': {'hidden': True}, 'b': {'hidden': True}, 'c': {'hidden': True}}
    """
    return {key: value_data for key in values}


def stringify_uuids(value: Any) -> Any:
    """
    Recursively convert UUID objects to strings in nested data structures.

    Handles:
    - Dict: Recursively processes all values
    - List: Recursively processes all items (except strings)
    - UUID: Converts to string
    - Other: Returns as-is

    Args:
        value: Data structure to process

    Returns:
        Data structure with UUIDs converted to strings

    Example:
        >>> import uuid
        >>> data = {'id': uuid.uuid4(), 'items': [uuid.uuid4(), 'text']}
        >>> stringify_uuids(data)
        {'id': '550e8400-e29b-41d4-a716-446655440000', 'items': ['550e8400-e29b-41d4-a716-446655440001', 'text']}
    """
    if isinstance(value, dict):
        return {key: stringify_uuids(val) for key, val in value.items()}
    elif isinstance(value, list) and not isinstance(value, str):
        return [stringify_uuids(item) for item in value]
    elif isinstance(value, uuid.UUID):
        return str(value)

    return value


def is_valid_uuid(value: str) -> bool:
    """
    Check if string is a valid UUID.

    Args:
        value: String to validate as UUID

    Returns:
        True if string is a valid UUID, False otherwise

    Example:
        >>> is_valid_uuid('550e8400-e29b-41d4-a716-446655440000')
        True
        >>> is_valid_uuid('invalid-uuid')
        False
    """
    if not isinstance(value, str):
        return False

    try:
        uuid.UUID(value)
        return True
    except (ValueError, TypeError):
        return False


def is_uuid(value: str) -> bool:
    """
    Alias for is_valid_uuid for backward compatibility.

    Args:
        value: String to validate as UUID

    Returns:
        True if string is a valid UUID, False otherwise
    """
    return is_valid_uuid(value)


def safe_uuid_convert(value: Any) -> Union[uuid.UUID, None]:
    """
    Safely convert value to UUID object.

    Args:
        value: Value to convert to UUID

    Returns:
        UUID object if conversion successful, None otherwise

    Example:
        >>> safe_uuid_convert('550e8400-e29b-41d4-a716-446655440000')
        UUID('550e8400-e29b-41d4-a716-446655440000')
        >>> safe_uuid_convert('invalid')
        None
    """
    if isinstance(value, uuid.UUID):
        return value

    if not isinstance(value, str):
        return None

    try:
        return uuid.UUID(value)
    except (ValueError, TypeError):
        return None


def normalize_pk_value(value: Any) -> Any:
    """
    Normalize primary key value for consistent comparison.

    Handles various PK types:
    - UUID: Converts to string
    - String: Strips whitespace
    - Other: Returns as-is

    Args:
        value: Primary key value to normalize

    Returns:
        Normalized primary key value
    """
    if isinstance(value, uuid.UUID):
        return str(value)
    elif isinstance(value, str):
        return value.strip()

    return value


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries, with dict2 values taking precedence.

    Args:
        dict1: Base dictionary
        dict2: Dictionary to merge into base

    Returns:
        Merged dictionary

    Example:
        >>> dict1 = {'a': 1, 'nested': {'x': 10, 'y': 20}}
        >>> dict2 = {'b': 2, 'nested': {'y': 30, 'z': 40}}
        >>> deep_merge_dicts(dict1, dict2)
        {'a': 1, 'b': 2, 'nested': {'x': 10, 'y': 30, 'z': 40}}
    """
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result
