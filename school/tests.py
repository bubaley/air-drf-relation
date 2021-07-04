from django.test import TestCase

from school.models import School, Cabinet, Child
from school.serializers import SchoolDefaultNestedSerializer, SchoolCustomNestedSerializer, SchoolAutoNestedSerializer


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
