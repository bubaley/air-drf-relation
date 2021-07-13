from uuid import uuid4

from django.db import models


class Child(models.Model):
    name = models.CharField(max_length=256)


class Cabinet(models.Model):
    name = models.CharField(max_length=256)
    code = models.IntegerField()
    school = models.ForeignKey('School', on_delete=models.CASCADE, related_name='cabinets')


class Floor(models.Model):
    uuid = models.UUIDField(default=uuid4, editable=True, primary_key=True, unique=True)
    name = models.CharField(max_length=255)
    school = models.ForeignKey('School', on_delete=models.CASCADE, related_name='floors')


class School(models.Model):
    name = models.CharField(max_length=256)
    children = models.ManyToManyField(Child, related_name='schools')


class Parent(models.Model):
    id = None
    uuid = models.UUIDField(default=uuid4, editable=True, primary_key=True, unique=True)
    name = models.CharField(max_length=128, unique=True)
