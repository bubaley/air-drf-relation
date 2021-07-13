from uuid import uuid4

from django.test import TestCase
from rest_framework.exceptions import ValidationError

from school.models import School, Floor
from school.serializers import SchoolDefaultNestedSerializer, SchoolCustomNestedSerializer, \
    SchoolAutoNestedSerializer, ParentCreateByPkSerializer, SchoolAutoNestedWithFloorSerializer


class SchoolTest(TestCase):
    def setUp(self) -> None:
        self.data = {
            'name': 'nested_creation',
            'cabinets': [
                {'name': 'cabinet', 'code': 1},
                {'name': 'second cabinet', 'code': 2},
            ]
        }

    def test_default_nested_creation(self):
        serializer = SchoolDefaultNestedSerializer(data=self.data)
        serializer.is_valid(raise_exception=True)
        instance: School = serializer.save()
        self.assertEqual(instance.cabinets.count(), 2)

    def test_custom_nested_creation(self):
        serializer = SchoolCustomNestedSerializer(data=self.data)
        serializer.is_valid(raise_exception=True)
        instance: School = serializer.save()
        self.assertEqual(instance.cabinets.count(), 2)

    def test_auto_nested_creation(self):
        serializer = SchoolAutoNestedSerializer(data=self.data)
        serializer.is_valid(raise_exception=True)
        instance: School = serializer.save()
        self.assertEqual(instance.cabinets.count(), 2)

    def test_auto_nested_with_uuid_creation(self):
        school = School.objects.create(name='nested_creation')
        floor = Floor.objects.create(school=school, name='first')
        data = {
            'name': 'nested_creation',
            'floors': [
                {'name': 'first', 'uuid': str(floor.uuid)},
                {'name': 'second'},
            ]
        }
        serializer = SchoolAutoNestedWithFloorSerializer(instance=school, data=data)
        serializer.is_valid(raise_exception=True)
        instance: School = serializer.save()
        self.assertEqual(instance.floors.count(), 2)


class ParentTest(TestCase):
    def setUp(self) -> None:
        self.uuid = str(uuid4())
        self.data = {'uuid': self.uuid, 'name': 'demo name'}

    def test_creation_with_unique_name(self):
        serializer = ParentCreateByPkSerializer(data=self.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = ParentCreateByPkSerializer(data=self.data)
        self.assertRaises(ValidationError, serializer.is_valid, raise_exception=True)

    def test_creation_with_pk(self):
        serializer = ParentCreateByPkSerializer(data=self.data, extra_kwargs={'uuid': {'read_only': False}})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.assertEqual(str(instance.pk), self.uuid)

        serializer = ParentCreateByPkSerializer(data=self.data, extra_kwargs={'uuid': {'read_only': False}})
        self.assertRaises(ValidationError, serializer.is_valid, raise_exception=True)
