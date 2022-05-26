from django.db import models


class Color(models.Model):
    name = models.CharField(max_length=256)


class Company(models.Model):
    name = models.CharField(max_length=256)


class Material(models.Model):
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='materials')
    name = models.CharField(max_length=256)


class Leg(models.Model):
    name = models.CharField(max_length=256)
    color = models.ForeignKey('Color', on_delete=models.CASCADE, related_name='legs')
    material = models.ForeignKey('Material', on_delete=models.CASCADE, related_name='legs')


class Table(models.Model):
    name = models.CharField(max_length=256)
    color = models.ForeignKey('Color', on_delete=models.CASCADE, related_name='tables')
    material = models.ForeignKey('Material', on_delete=models.CASCADE, related_name='tables')
    legs = models.ManyToManyField('Leg', related_name='tables')
