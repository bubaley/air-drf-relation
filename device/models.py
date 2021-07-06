from django.db import models


class Device(models.Model):
    name = models.CharField(max_length=128, null=True)
    code = models.IntegerField(null=True)
    text = models.TextField(null=True)
    model = models.CharField(max_length=128, null=True)
