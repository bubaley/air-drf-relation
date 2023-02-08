from django.db.models import QuerySet, Case, When
from rest_framework import serializers
from django.db import models


def optimize_queryset(queryset, serializer):
    if queryset is None:
        return queryset
    queryset_type = type(queryset)
    data = get_relations(serializer)
    if issubclass(queryset_type, models.Model):
        queryset = serializer.Meta.model.objects.filter(pk=queryset.pk)
        queryset = queryset.select_related(*data['select']).prefetch_related(*data['prefetch']).first()
    elif issubclass(queryset_type, QuerySet):
        queryset = queryset.select_related(*data['select']).prefetch_related(*data['prefetch'])
    elif issubclass(queryset_type, list):
        pks = [v.pk for v in queryset]
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(pks)])
        queryset = serializer.Meta.model.objects.filter(pk__in=pks).order_by(preserved)
        queryset = queryset.select_related(*data['select']).prefetch_related(*data['prefetch'])
    return queryset


def get_relations(serializer) -> dict:
    return _get_relations(serializer)


def _get_relations(serializer, to_prefetch=False) -> dict:
    results = {'select': [], 'prefetch': []}
    _serializer = serializer() if type(serializer) == serializers.SerializerMetaclass else serializer
    if not issubclass(type(_serializer), serializers.ModelSerializer):
        return results
    model_fields = [v.name for v in _serializer.Meta.model._meta.get_fields()]
    for field, value in _serializer.fields.fields.items():
        if field not in model_fields or value.write_only:
            continue
        field_serializer, field_to_prefetch = _get_field_serializer(value)
        prefetch = to_prefetch or field_to_prefetch
        if not field_serializer:
            continue
        relations = _get_relations(field_serializer, prefetch)
        _append_relations_to_results(results, relations, field, prefetch)
    return results


def _get_field_serializer(value):
    current_type = type(value)
    if issubclass(current_type, serializers.PrimaryKeyRelatedField) and hasattr(value, 'serializer'):
        return value.serializer, False
    elif issubclass(current_type, serializers.ModelSerializer):
        return value, False
    elif issubclass(current_type, serializers.ListSerializer):
        return value.child, True
    elif issubclass(current_type, serializers.ManyRelatedField):
        if hasattr(value.child_relation, 'serializer'):
            return value.child_relation.serializer, True
    return None, False


def _append_relations_to_results(results, relations, field_name, prefetch):
    if not relations['select'] and not relations['prefetch']:
        if prefetch:
            results['prefetch'].append(field_name)
        else:
            results['select'].append(field_name)
    else:
        results['select'] += [f'{field_name}__{v}' for v in relations['select']]
        results['prefetch'] += [f'{field_name}__{v}' for v in relations['prefetch']]
        if not prefetch and not relations['select']:
            results['select'].append(field_name)
