from dataclasses import dataclass

from django.db import models

from air_drf_relation.fields import AirDataclassField


@dataclass
class FilmInformation:
    budget: float
    rating: str
    description: str
    active: bool = True
    # kek: int = 1


class Actor(models.Model):
    name = models.CharField(max_length=256)


class Film(models.Model):
    name = models.CharField(max_length=256)
    release_date = models.DateField()
    information: FilmInformation = AirDataclassField(data_class=FilmInformation)
    actors = models.ManyToManyField(Actor, related_name='films')
