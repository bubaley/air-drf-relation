from typing import Any, Dict, List, Optional, Tuple, Type, Union

from django.db import models
from django.db.models import Case, QuerySet, When
from rest_framework import serializers


def optimize_queryset(
    queryset: Union[models.Model, QuerySet, List[models.Model], None],
    serializer: Union[serializers.ModelSerializer, Type[serializers.ModelSerializer]],
) -> Union[models.Model, QuerySet, None]:
    """
    Optimize queryset by adding select_related and prefetch_related based on serializer structure.

    Args:
        queryset: QuerySet, Model instance, list of models, or None
        serializer: ModelSerializer instance or class

    Returns:
        Optimized queryset with proper select_related and prefetch_related
    """
    if queryset is None:
        return queryset

    relations = get_relations(serializer)

    if isinstance(queryset, models.Model):
        return _optimize_single_model(queryset, serializer, relations)
    elif isinstance(queryset, QuerySet):
        return _optimize_queryset(queryset, relations)
    elif isinstance(queryset, list):
        return _optimize_model_list(queryset, serializer, relations)

    return queryset


def get_relations(
    serializer: Union[serializers.ModelSerializer, Type[serializers.ModelSerializer]],
) -> Dict[str, List[str]]:
    """
    Extract select_related and prefetch_related relations from serializer structure.

    Args:
        serializer: ModelSerializer instance or class

    Returns:
        Dictionary with 'select' and 'prefetch' keys containing relation lists
    """
    return _extract_relations(serializer, is_prefetch=False)


def _optimize_single_model(
    model_instance: models.Model,
    serializer: Union[serializers.ModelSerializer, Type[serializers.ModelSerializer]],
    relations: Dict[str, List[str]],
) -> Optional[models.Model]:
    """
    Optimize a single model instance by creating an optimized queryset.

    Args:
        model_instance: Single model instance
        serializer: ModelSerializer instance or class
        relations: Relations dictionary from get_relations

    Returns:
        Optimized model instance
    """
    serializer_instance = _get_serializer_instance(serializer)
    model_class = serializer_instance.Meta.model

    queryset = model_class.objects.filter(pk=model_instance.pk)
    optimized_queryset = _apply_optimizations(queryset, relations)

    return optimized_queryset.first()


def _optimize_queryset(queryset: QuerySet, relations: Dict[str, List[str]]) -> QuerySet:
    """
    Optimize existing QuerySet by adding relations.

    Args:
        queryset: QuerySet to optimize
        relations: Relations dictionary from get_relations

    Returns:
        Optimized QuerySet
    """
    return _apply_optimizations(queryset, relations)


def _optimize_model_list(
    model_list: List[models.Model],
    serializer: Union[serializers.ModelSerializer, Type[serializers.ModelSerializer]],
    relations: Dict[str, List[str]],
) -> QuerySet:
    """
    Optimize a list of model instances by creating a preserved-order QuerySet.

    Args:
        model_list: List of model instances
        serializer: ModelSerializer instance or class
        relations: Relations dictionary from get_relations

    Returns:
        Optimized QuerySet with preserved order
    """
    if not model_list:
        return model_list

    serializer_instance = _get_serializer_instance(serializer)
    model_class = serializer_instance.Meta.model

    pks = [instance.pk for instance in model_list]
    preserved_order = _create_preserved_case(pks)

    queryset = model_class.objects.filter(pk__in=pks).order_by(preserved_order)
    return _apply_optimizations(queryset, relations)


def _apply_optimizations(queryset: QuerySet, relations: Dict[str, List[str]]) -> QuerySet:
    """
    Apply select_related and prefetch_related optimizations to QuerySet.

    Args:
        queryset: QuerySet to optimize
        relations: Relations dictionary with select and prefetch lists

    Returns:
        Optimized QuerySet
    """
    if relations['select']:
        queryset = queryset.select_related(*relations['select'])

    if relations['prefetch']:
        queryset = queryset.prefetch_related(*relations['prefetch'])

    return queryset


def _create_preserved_case(pks: List[Any]) -> Case:
    """
    Create a Case expression to preserve the order of PKs in QuerySet.

    Args:
        pks: List of primary key values

    Returns:
        Case expression for ordering
    """
    return Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(pks)])


def _get_serializer_instance(
    serializer: Union[serializers.ModelSerializer, Type[serializers.ModelSerializer]],
) -> serializers.ModelSerializer:
    """
    Get serializer instance from class or instance.

    Args:
        serializer: Serializer class or instance

    Returns:
        Serializer instance
    """
    return serializer() if isinstance(serializer, type) else serializer


def _extract_relations(
    serializer: Union[serializers.ModelSerializer, Type[serializers.ModelSerializer]], is_prefetch: bool = False
) -> Dict[str, List[str]]:
    """
    Recursively extract relations from serializer fields.

    Args:
        serializer: ModelSerializer instance or class
        is_prefetch: Whether current context requires prefetch_related

    Returns:
        Dictionary with 'select' and 'prefetch' keys containing relation lists
    """
    results = {'select': [], 'prefetch': []}

    serializer_instance = _get_serializer_instance(serializer)

    if not isinstance(serializer_instance, serializers.ModelSerializer):
        return results

    model_fields = _get_model_field_names(serializer_instance)

    for field_name, field_instance in serializer_instance.fields.items():
        if not _should_process_field(field_name, field_instance, model_fields):
            continue

        field_serializer, field_requires_prefetch = _analyze_field(field_instance)
        if not field_serializer:
            continue

        current_prefetch = is_prefetch or field_requires_prefetch
        nested_relations = _extract_relations(field_serializer, current_prefetch)

        _merge_relations(results, nested_relations, field_name, current_prefetch)

    return results


def _get_model_field_names(serializer: serializers.ModelSerializer) -> List[str]:
    """
    Get list of model field names from serializer Meta.

    Args:
        serializer: ModelSerializer instance

    Returns:
        List of model field names
    """
    return [field.name for field in serializer.Meta.model._meta.get_fields()]


def _should_process_field(field_name: str, field_instance: serializers.Field, model_fields: List[str]) -> bool:
    """
    Check if field should be processed for optimization.

    Args:
        field_name: Name of the field
        field_instance: Field instance
        model_fields: List of model field names

    Returns:
        True if field should be processed
    """
    return field_name in model_fields and not field_instance.write_only


def _analyze_field(field_instance: serializers.Field) -> Tuple[Optional[serializers.BaseSerializer], bool]:
    """
    Analyze field to determine if it contains a nested serializer and if it requires prefetch.

    Args:
        field_instance: Field instance to analyze

    Returns:
        Tuple of (nested_serializer, requires_prefetch)
    """
    field_type = type(field_instance)

    # PrimaryKeyRelatedField with custom serializer
    if issubclass(field_type, serializers.PrimaryKeyRelatedField) and hasattr(field_instance, 'serializer'):
        return field_instance.serializer, False

    # Direct ModelSerializer
    if issubclass(field_type, serializers.ModelSerializer):
        return field_instance, False

    # ListSerializer (many=True)
    if issubclass(field_type, serializers.ListSerializer):
        return field_instance.child, True

    # ManyRelatedField
    if (
        issubclass(field_type, serializers.ManyRelatedField)
        and hasattr(field_instance, 'child_relation')
        and hasattr(field_instance.child_relation, 'serializer')
    ):
        return field_instance.child_relation.serializer, True

    return None, False


def _merge_relations(
    results: Dict[str, List[str]], nested_relations: Dict[str, List[str]], field_name: str, use_prefetch: bool
) -> None:
    """
    Merge nested relations into main results dictionary.

    Args:
        results: Main results dictionary to merge into
        nested_relations: Nested relations to merge
        field_name: Current field name
        use_prefetch: Whether to use prefetch_related for this field
    """
    if not nested_relations['select'] and not nested_relations['prefetch']:
        # Simple relation without nested relations
        if use_prefetch:
            results['prefetch'].append(field_name)
        else:
            results['select'].append(field_name)
    else:
        # Complex relation with nested relations
        _merge_nested_relations(results, nested_relations, field_name, use_prefetch)


def _merge_nested_relations(
    results: Dict[str, List[str]], nested_relations: Dict[str, List[str]], field_name: str, use_prefetch: bool
) -> None:
    """
    Merge complex nested relations with proper prefixes.

    Args:
        results: Main results dictionary to merge into
        nested_relations: Nested relations to merge
        field_name: Current field name
        use_prefetch: Whether to use prefetch_related for this field
    """
    # Add prefixed nested select relations
    results['select'].extend([f'{field_name}__{relation}' for relation in nested_relations['select']])

    # Add prefixed nested prefetch relations
    results['prefetch'].extend([f'{field_name}__{relation}' for relation in nested_relations['prefetch']])

    # Add base field to select if not using prefetch and no select relations
    if not use_prefetch and not nested_relations['select']:
        results['select'].append(field_name)
