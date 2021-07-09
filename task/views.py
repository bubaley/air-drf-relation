from django.http import HttpRequest
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from django.conf import settings

from .models import Task
from .serializers import TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    @action(methods=['PUT'], detail=True)
    def set_image(self, request, pk=None):
        instance: Task = self.get_object()
        file = request.data.get('image')
        instance.image.save(name=file.name, content=file)
        return Response(self.get_serializer(instance).data)

    @action(methods=['GET'], detail=True)
    def get_without_context(self, request, pk=None):
        instance: Task = self.get_object()
        data = TaskSerializer([instance], many=True).data
        return Response(data)
