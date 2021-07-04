from django.db import models


class Child(models.Model):
    name = models.CharField(max_length=256)


class Cabinet(models.Model):
    name = models.CharField(max_length=256)
    code = models.IntegerField()
    school = models.ForeignKey('School', on_delete=models.CASCADE, related_name='cabinets')


class School(models.Model):
    name = models.CharField(max_length=256)
    children = models.ManyToManyField(Child, related_name='schools')
