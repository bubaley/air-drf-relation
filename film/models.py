from dataclasses import dataclass

from django.db import models

from air_drf_relation.model_fields import AirDataclassField


@dataclass
class FilmInformation:
    rating: str
    description: str
    budget: float = 0
    active: bool = True


class Actor(models.Model):
    name = models.CharField(max_length=256)


class Film(models.Model):
    name = models.CharField(max_length=256)
    release_date = models.DateField()
    information: FilmInformation = AirDataclassField(data_class=FilmInformation)
    actors = models.ManyToManyField(Actor, related_name='films')
