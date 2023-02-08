from datetime import datetime
from random import randint
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from film.models import Actor, Film, FilmInformation
from film.serializers import FilmSerializer
from django.conf import settings

settings.DEBUG = True


class ValidatePreload(TestCase):
    def setUp(self) -> None:
        Actor.objects.bulk_create([Actor(name=v) for v in range(5)])
        FilmInformation(description='123', budget=123, rating='123')
        self.film = Film.objects.create(name='demo', release_date=datetime.utcnow().date())
        self.film.actors.set(Actor.objects.all())

    def test_to_representation(self):
        result = FilmSerializer(self.film).data
        self.assertEqual(result['information'], None)
        self.film.information = FilmInformation(1, '1', '1')
        self.film.save()
        # self.film.information = {'budget': 1}
        # self.film.save()
        # self.film.refresh_from_db()
        information = FilmSerializer(self.film).data['information']
        # keys = ['rating', 'description']
        # values = [getattr(information, v) for v in keys]
        # self.assertEqual(values, [None], None)

    def test_validation(self):
        data = {'name': 'demo', 'release_date': '2021-01-01', 'actors': [], 'information': {}}
        # serializer = FilmSerializer(data=data)
        # self.assertRaises(ValidationError, serializer.is_valid, True)
        data['information'] = {'budget': 1, 'rating': 1, 'description': '1', 'active': False}
        serializer = FilmSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance: Film = serializer.save()
        self.assertEqual(type(instance.information), FilmInformation)
        self.assertEqual(instance.information.active, False)
        data['information'].pop('active', None)
        serializer = FilmSerializer(instance=instance, data=data)
        serializer.is_valid(raise_exception=True)
        instance: Film = serializer.save()
        self.assertEqual(instance.information.active, False)
