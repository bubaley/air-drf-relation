from django.conf import settings
from django.test import TestCase, override_settings

from task.models import Tag, Task
from task.serializers import TaskSerializer


class TestFullImageUrl(TestCase):
    def setUp(self) -> None:
        self.path = '/media/image.png'
        self.task = Task.objects.create(name='demo', image='/image.png')
        self.tag = Tag.objects.create(task=self.task, name='demo', image='/image.png')

    def test_default_image_path(self):
        result = TaskSerializer(self.task).data
        path = get_path() + self.path
        self.assertEqual(result['image'], path)

    @override_settings(AIR_DRF_RELATION={'HTTP_HOST': '127.0.0.1:8000', 'USE_SSL': True, 'USE_PRELOAD': True})
    def test_https(self):
        result = TaskSerializer(self.task).data
        path = get_path() + self.path
        self.assertEqual(result['image'], path)

    @override_settings(AIR_DRF_RELATION={'HTTP_HOST': 'demo.com', 'USE_SSL': False, 'USE_PRELOAD': True})
    def test_custom_host(self):
        path = get_path() + self.path
        result = TaskSerializer(self.task).data
        self.assertEqual(result['image'], path)

    def test_many_serializer(self):
        data = TaskSerializer([self.task], many=True).data
        self.assertEqual(len(data), 1)


def get_path():
    current_settings = settings.AIR_DRF_RELATION
    host = current_settings.get('HTTP_HOST')
    use_ssl = current_settings.get('USE_SSL')
    return f'{"https" if use_ssl else "http"}://{host}'
