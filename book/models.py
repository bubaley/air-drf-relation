from uuid import uuid4

from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=128)
    active = models.BooleanField(default=True)


class City(models.Model):
    id = None
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=128)
    active = models.BooleanField(default=True)


class Book(models.Model):
    id = None
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=128)
    author = models.ForeignKey(Author, related_name='books', on_delete=models.CASCADE, null=True)
    city = models.ForeignKey(City, related_name='books', on_delete=models.CASCADE, null=True)
    active = models.BooleanField(default=True)


class Magazine(models.Model):
    name = models.CharField(max_length=255)
    author = models.ForeignKey(Author, related_name='magazines', on_delete=models.CASCADE)
    city = models.ForeignKey(City, related_name='magazines', on_delete=models.CASCADE)
