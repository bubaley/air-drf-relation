from django.db import models


class Task(models.Model):
    name = models.CharField(max_length=128)
    image = models.ImageField(upload_to='images/', null=True)
