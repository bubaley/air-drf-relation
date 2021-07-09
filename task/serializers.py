from rest_framework import serializers

from air_drf_relation.serializers import AirModelSerializer
from .models import Task


class TaskSerializer(AirModelSerializer):
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Task
        fields = ('id', 'name', 'image')
