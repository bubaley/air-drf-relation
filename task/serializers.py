from air_drf_relation.fields import AirRelatedField
from air_drf_relation.serializers import AirModelSerializer
from .models import Task, Tag


class TagSerializer(AirModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'image')


class TaskSerializer(AirModelSerializer):
    tags = AirRelatedField(TagSerializer, many=True, read_only=True)

    class Meta:
        model = Task
        fields = ('id', 'name', 'image', 'tags')
