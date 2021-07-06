from django.test import TestCase

from device.serializers import DeviceWithoutActionsSerializer, DeviceWithReadOnlyActionsSerializer, \
    DeviceWithHiddenActionsSerializer


class DeviceTest(TestCase):
    def setUp(self) -> None:
        self.data = {
            'name': 'name',
            'code': 1,
            'text': 'text',
            'model': 'model'
        }

    def test_creation_without_actions(self):
        serializer = DeviceWithoutActionsSerializer(data=self.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = serializer.data
        self.assertEqual(data['text'], None)
        self.assertEqual(data['model'], None)
        self.assertEqual('name' not in data, True)
        self.assertEqual('code' not in data, True)
        self.assertEqual(len(data), 3)

    def test_creation_with_read_only_actions(self):
        serializer = DeviceWithReadOnlyActionsSerializer(data=self.data, action='create')
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = serializer.data
        self.assertEqual(data['name'], None)
        self.assertEqual(data['code'], None)

        serializer = DeviceWithReadOnlyActionsSerializer(data=self.data, action='custom_action')
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = serializer.data
        self.assertEqual(data['model'], None)
        self.assertEqual(data['code'], self.data['code'])
        self.assertEqual(data['name'], self.data['name'])

    def test_creation_with_hidden_action(self):
        serializer = DeviceWithHiddenActionsSerializer(data=self.data, action='update')
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = serializer.data
        self.assertEqual('id' not in data, True)

        serializer = DeviceWithHiddenActionsSerializer(data=self.data, action='custom_action')
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = serializer.data
        self.assertEqual(len(data), 1)

        extra_kwargs = {
            'name': {'hidden': False},
            'code': {'hidden': False},
        }
        serializer = DeviceWithHiddenActionsSerializer(data=self.data, action='custom_action',
                                                       extra_kwargs=extra_kwargs)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = serializer.data
        self.assertEqual(len(data), 3)
