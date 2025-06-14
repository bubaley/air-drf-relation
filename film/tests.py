from datetime import datetime

from django.conf import settings
from django.test import TestCase

from film.models import Actor, Film, FilmInformation
from film.serializers import FilmSerializer

settings.DEBUG = True


class ValidatePreload(TestCase):
    def setUp(self) -> None:
        Actor.objects.bulk_create([Actor(name=v) for v in range(5)])
        inf = FilmInformation(description='123', budget=123, rating='123')
        self.film = Film.objects.create(name='demo', release_date=datetime.now().date(), information=inf)
        self.film.actors.set(Actor.objects.all())

    def test_to_representation(self):
        _ = FilmSerializer(self.film).data
        information = FilmInformation(1, '1', '1')
        self.film.information = information
        self.film.save()

    def test_validation(self):
        data = {'name': 'demo', 'release_date': '2021-01-01', 'actors': [], 'information': {}}
        data['information'] = {'budget': 100, 'rating': 1, 'description': '1', 'active': False}
        serializer = FilmSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance: Film = serializer.save()
        self.assertEqual(type(instance.information), FilmInformation)
        self.assertEqual(instance.information.active, False)
        data['information'].pop('active', None)
        data['information'].pop('budget', None)
        serializer = FilmSerializer(instance=instance, data=data)
        serializer.is_valid(raise_exception=True)
        instance: Film = serializer.save()
        self.assertEqual(instance.information.active, False)
        self.assertEqual(instance.information.budget, 100)
