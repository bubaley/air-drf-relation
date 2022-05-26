from random import randint
from django.test import TestCase
from air_drf_relation.preload_objects_manager import PreloadObjectsManager
from table.models import Material, Table, Company, Color, Leg
from table.serializers import TableSerializer, TableWithLegsSerializer
from air_drf_relation.decorators import queries_count
from django.conf import settings
from django.db import reset_queries, connection

settings.DEBUG = True


class ValidatePreload(TestCase):
    def setUp(self) -> None:
        self._materials_count = 20
        self._colors_count = 20
        self._companies_count = 5
        self._legs_count = 50
        self._table_count = 1000
        Company.objects.bulk_create([Company(name=v) for v in range(self._companies_count)])
        Leg.objects.bulk_create(
            [Leg(name=v, color_id=get_id(self._colors_count), material_id=get_id(self._materials_count)) for v in
             range(self._legs_count)])
        Material.objects.bulk_create(
            [Material(name=v, company_id=get_id(self._companies_count)) for v in range(self._materials_count)])
        Color.objects.bulk_create([Color(name=v) for v in range(self._colors_count)])
        Table.objects.bulk_create(
            [Table(name=v, material_id=get_id(self._materials_count), color_id=get_id(self._colors_count)) for v in
             range(self._table_count)])

        self.data = [
            {'name': v, 'material': {'company': get_id(self._companies_count)}, 'color': get_id(self._colors_count),
             'legs': [get_id(self._legs_count) for _ in range(5)]} for v in range(self._table_count)]
        reset_queries()

    @queries_count
    def test_optimize_validate_preload(self):
        data = [{'name': v, 'material': {'company': get_id(self._companies_count)}, 'color': get_id(self._colors_count),
                 'legs': [get_id(self._legs_count) for _ in range(5)]} for v in range(self._table_count)]
        serializer = TableSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)

    @queries_count
    def test_preload_objects_manager(self):
        reset_queries()
        self.data[0]['color'] = 'failed_pk'
        serializer = TableSerializer(data=self.data, many=True)
        result = PreloadObjectsManager(serializer).init()
        colors_len = len(list(set([v['color'] for v in self.data])))
        colors_hash = PreloadObjectsManager.hash_from_queryset(Color)
        legs = []
        for el in self.data:
            legs += el['legs']
        legs_len = len(list(set(legs)))
        legs_hash = PreloadObjectsManager.hash_from_queryset(Leg)
        companies_len = len(list(set([v['material']['company'] for v in self.data])))
        companies_hash = PreloadObjectsManager.hash_from_queryset(Company)
        self.assertEqual(len(result.preloaded_objects[colors_hash]), colors_len - 1)
        self.assertEqual(len(result.preloaded_objects[legs_hash]), legs_len)
        self.assertEqual(len(result.preloaded_objects[companies_hash]), companies_len)
        self.assertEqual(len(connection.queries), 3)
        self.data[0]['color'] = get_id(self._colors_count)
        reset_queries()
        serializer.is_valid(raise_exception=True)
        self.assertEqual(len(connection.queries), 3)

    @queries_count
    def test_optimize_with_many_serializer(self):
        data = [{'name': v, 'material': get_id(self._materials_count), 'color': get_id(self._colors_count),
                 'legs': [{'color': get_id(self._colors_count), 'name': '1', 'code': 1} for _ in range(5)]} for v in
                range(self._table_count)]
        serializer = TableWithLegsSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        self.assertEqual(len(connection.queries), 2)

    @queries_count
    def test_toogle_preload_objects(self):
        data = [{'name': v, 'material': get_id(self._materials_count), 'color': get_id(self._colors_count),
                 'legs': [{'color': get_id(self._colors_count), 'name': '1', 'code': 1} for _ in range(5)]} for v in
                range(300)]
        PreloadObjectsManager.disable_search_for_preloaded_objects()
        serializer = TableWithLegsSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        self.assertGreater(len(connection.queries), 2000)
        PreloadObjectsManager.enable_search_for_preloaded_objects()
        serializer = TableWithLegsSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        self.assertGreater(len(connection.queries), 2)


def get_id(count):
    return randint(1, count)
