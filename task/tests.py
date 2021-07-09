from django.test import TestCase

from task.models import Task, Tag
from task.serializers import TaskSerializer
from django.conf import settings


class TestFullImageUrl(TestCase):
    def setUp(self) -> None:
        self.path = '/media/image.png'
        self.task = Task.objects.create(name='demo', image='/image.png')
        self.tag = Tag.objects.create(task=self.task, name='demo', image='/image.png')

    def test_default_image_path(self):
        result = TaskSerializer(self.task).data
        path = get_path() + self.path
        self.assertEqual(result['image'], path)

    def test_https(self):
        settings.AIR_DRF_RELATION['USE_SSL'] = True
        result = TaskSerializer(self.task).data
        path = get_path() + self.path
        self.assertEqual(result['image'], path)

    def test_custom_host(self):
        settings.AIR_DRF_RELATION['HTTP_HOST'] = 'demo.com'
        path = get_path() + self.path
        result = TaskSerializer(self.task).data
        self.assertEqual(result['image'], path)

    def test_many_serializer(self):
        data = TaskSerializer([self.task], many=True).data
        pass


def get_path():
    current_settings = settings.AIR_DRF_RELATION
    host = current_settings.get('HTTP_HOST')
    use_ssl = current_settings.get('USE_SSL')
    return f'{"https" if use_ssl else "http"}://{host}'
