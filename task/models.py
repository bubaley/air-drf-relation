from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=128, null=True)
    image = models.ImageField(upload_to='images/', null=True)
    task = models.ForeignKey('Task', related_name='tags', on_delete=models.CASCADE)


class Task(models.Model):
    name = models.CharField(max_length=128)
    image = models.ImageField(upload_to='images/', null=True)
