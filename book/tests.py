from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import User
from django.db import connection, reset_queries
from django.test import TestCase
from rest_framework import serializers

from air_drf_relation.decorators import queries_count
from air_drf_relation.queryset_optimization import get_relations
from air_drf_relation.serializers import AirDynamicSerializer

from .filters import AuthorFilter
from .models import Author, Book, Bookmark, City, Genre, Magazine
from .serializers import (
    BookActionKwargsSerializer,
    BookHiddenSerializer,
    BookmarkSerializer,
    BookReadOnlySerializer,
    BookSerializer,
    BookWithGenreListSerializer,
    BookWithGenreSerializer,
    CityWritablePkSerializer,
    DefaultBookSerializer,
    DefaultMagazineSerializer,
    DisableOptimizationBookSerializer,
    MagazineSerializer,
    MagazineSpecialSerializer,
)

settings.DEBUG = True


class TestBookObjects(TestCase):
    def setUp(self) -> None:
        self.author = Author.objects.create(name='author')
        self.author2 = Author.objects.create(name='second author')
        self.author3 = Author.objects.create(name='inactive author', active=False)
        self.city = City.objects.create(name='city')
        self.city2 = City.objects.create(name='second city')
        self.city3 = City.objects.create(name='inactive city', active=False)
        self.book = Book.objects.create(name='book', author=self.author, city=self.city)

    def test_default_book_serializer(self):
        serializer = DefaultBookSerializer(data={'name': 'default serializer creation'})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.assertEqual(instance.author, None)
        self.assertEqual(instance.city, None)

    def test_default_creation(self):
        serializer = BookSerializer(data={'name': 'default creation'}, context=None)
        serializer.is_valid(raise_exception=True)
        instance: Book = serializer.save()
        self.assertEqual(instance.author, None)
        self.assertEqual(instance.city, None)
        self.assertEqual(serializer.data['author'], None)
        self.assertEqual(serializer.data['city'], None)

    def test_default_serialization(self):
        data = BookSerializer(self.book).data
        self.assertIsInstance(data['author'], dict)
        self.assertIsInstance(data['city'], dict)

    def test_pk_serialization(self):
        extra_kwargs = {'author': {'pk_only': True}, 'city': {'pk_only': True}}
        data = BookSerializer(self.book, extra_kwargs=extra_kwargs).data
        self.assertEqual(type(data['author']), int)
        self.assertEqual(type(data['city']), str)

    def test_required_creation(self):
        data = {'name': 'required and allow null creation'}
        extra_kwargs = {'author': {'required': True}, 'city': {'required': True}}
        serializer = BookSerializer(data=data, extra_kwargs=extra_kwargs)
        serializer.is_valid()
        self.assertEqual(len(serializer.errors), 2)

        data['author'] = None
        data['city'] = None
        extra_kwargs['author']['allow_null'] = True
        extra_kwargs['city']['allow_null'] = False

        serializer = BookSerializer(data=data, extra_kwargs=extra_kwargs)
        serializer.is_valid()
        self.assertEqual(len(serializer.errors), 1)

        data['city'] = str(self.city.pk)
        serializer = BookSerializer(data=data, extra_kwargs=extra_kwargs)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        self.assertEqual(instance.author, None)
        self.assertEqual(instance.city, self.city)
        self.assertEqual(serializer.data['author'], None)
        self.assertEqual(serializer.data['city']['uuid'], str(self.city.pk))

    def test_read_only_creation(self):
        extra_kwargs = {'author': {'read_only': True}, 'city': {'read_only': True}}
        data = {'name': 'read only creation', 'author': self.author.pk, 'city': str(self.city.pk)}
        serializer = BookSerializer(data=data, extra_kwargs=extra_kwargs)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.assertEqual(instance.author, None)
        self.assertEqual(instance.city, None)
        self.assertEqual(serializer.data['author'], None)
        self.assertEqual(serializer.data['city'], None)

    def test_read_only_as_default_kwargs_creation(self):
        data = {'name': 'read only as default kwargs', 'author': self.author.pk, 'city': str(self.city.pk)}
        serializer = BookReadOnlySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.assertEqual(instance.author, None)
        self.assertEqual(instance.city, None)
        self.assertEqual(serializer.data['author'], None)
        self.assertEqual(serializer.data['city'], None)

    def test_hidden_creation(self):
        data = {'name': 'hidden'}
        serializer = BookHiddenSerializer(data=data, extra_kwargs={'city': {'hidden': True}})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.assertEqual(instance.author, None)
        self.assertEqual(instance.city, None)
        self.assertEqual(serializer.data.get('author', False), False)
        self.assertEqual(serializer.data.get('name', False), False)
        self.assertEqual(serializer.data.get('city', False), False)

        result = DefaultBookSerializer(instance).data
        self.assertEqual(result['author'], None)
        self.assertEqual(result['name'], '')
        self.assertEqual(result['city'], None)

    def test_action_kwargs(self):
        data = {'name': 'hidden', 'city': str(self.city.pk), 'author': self.author.pk}
        serializer = BookActionKwargsSerializer(data=data, action='create')
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.assertEqual(instance.city, None)
        self.assertEqual(instance.author, self.author)
        self.assertEqual(serializer.data.get('city', False), False)

        serializer = BookActionKwargsSerializer(data=data, action='second_create')
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.assertEqual(serializer.data.get('name', False), False)
        self.assertEqual(instance.author, None)

    def test_queryset_creation(self):
        data = {'name': 'queryset', 'author': self.author3.pk, 'city': str(self.city3.pk)}
        serializer = BookSerializer(data=data)
        serializer.is_valid()
        self.assertEqual(len(serializer.errors), 2)

        data = {'name': 'queryset', 'author': self.author3.pk, 'city': str(self.city3.pk)}
        extra_kwargs = {'author': {'queryset_function_disabled': True}, 'city': {'queryset_function_disabled': True}}
        serializer = BookSerializer(data=data, extra_kwargs=extra_kwargs)
        serializer.is_valid()
        self.assertEqual(len(serializer.errors), 0)

    def test_create_from_dict(self):
        data = {'name': 'create from dict', 'author': {'id': self.author.pk}, 'city': {'uuid': str(self.city.uuid)}}
        serializer = BookSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.assertIsInstance(serializer.data['author'], dict)
        self.assertIsInstance(serializer.data['city'], dict)
        self.assertEqual(instance.author, self.author)
        self.assertEqual(instance.city, self.city)

    def test_many_to_many_save(self):
        Genre.objects.create(name='1', id=1)
        Genre.objects.create(name='2', id=2)

        data = {'name': 'many to many', 'genres': [1, {'id': 2}]}
        serializer = BookWithGenreSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.assertEqual(instance.genres.count(), 2)

    def test_set_user(self):
        user = User.objects.create(email='demo@demo.com')
        serializer = BookSerializer(data={'name': 'custom set user'}, user=user)
        self.assertEqual(serializer.user, user)

        class Request:
            def __init__(self, user):
                self.user = user

        serializer = BookSerializer(data={'name': 'custom set user'}, context={'request': Request(user=user)})
        self.assertEqual(serializer.user, user)


class TestMagazineObjects(TestCase):
    def setUp(self) -> None:
        self.author = Author.objects.create(name='author')
        self.author2 = Author.objects.create(name='inactive author', active=False)
        self.city = City.objects.create(name='city')
        self.city2 = City.objects.create(name='city2')

    def test_check_required_fields(self):
        data = {'name': 'magazine'}
        serializer = MagazineSerializer(data=data)
        serializer.is_valid()
        self.assertEqual(len(serializer.errors), 2)

        data['author'] = None
        data['city'] = None

        serializer = MagazineSerializer(data=data)
        serializer.is_valid()
        self.assertEqual(len(serializer.errors), 2)
        #
        extra_kwargs = {'city': {'allow_null': True}, 'author': {'allow_null': True}}
        serializer = MagazineSerializer(data=data, extra_kwargs=extra_kwargs)
        serializer.is_valid()
        self.assertEqual(len(serializer.errors), 0)
        self.assertRaises(Exception, serializer.save)

    def test_default_creation(self):
        data = {'name': 'default', 'author': self.author.pk, 'city': str(self.city.pk)}
        serializer = MagazineSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.assertEqual(instance.author, self.author)
        self.assertEqual(instance.city, self.city)
        data = MagazineSerializer(Magazine.objects.all(), many=True).data

    def test_special_creation(self):
        data = {'name': 'default', 'author': self.author2.pk, 'city': str(self.city.pk)}
        serializer = MagazineSpecialSerializer(data=data, context={'user': 1})
        serializer.is_valid()
        self.assertEqual(len(serializer.errors), 1)

    def test_writable_pk(self):
        data = {'uuid': None, 'name': 'writable pk'}
        actions = ['create', 'second_action']
        for action in actions:
            data['uuid'] = str(uuid4())
            serializer = CityWritablePkSerializer(data=data, action=action)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            self.assertEqual(str(instance.uuid), data['uuid'])

        data['uuid'] = str(uuid4())
        serializer = CityWritablePkSerializer(data=data, action='action_does_not_exists')
        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.data.get('name', False), False)

    def test_uuid_serialization(self):
        data = {
            'name': 'default',
            'author': self.author.pk,
            'city': str(self.city.pk),
            'available_cities': [
                str(self.city.pk),
                str(self.city2.pk),
            ],
        }
        extra_kwargs = {'city': {'pk_only': True}, 'author': {'pk_only': True}}
        serializer = DefaultMagazineSerializer(data=data, extra_kwargs=extra_kwargs)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.assertEqual(type(serializer.data['city']), str)
        self.assertTrue(all(isinstance(v, str) for v in serializer.data['available_cities']))


class TestOptimizeQuerySet(TestCase):
    def setUp(self) -> None:
        self.author = Author.objects.create(name='author')
        self.city = City.objects.create(name='city')
        self.city2 = City.objects.create(name='second city', parent_city=self.city)
        genre1 = Genre.objects.create(name='first', city=self.city)
        genre2 = Genre.objects.create(name='second', city=self.city2)
        genre3 = Genre.objects.create(name='second', city=self.city2)
        genre4 = Genre.objects.create(name='second', city=self.city2)
        genre5 = Genre.objects.create(name='second', city=self.city2)
        for el in range(100):
            self.book = Book.objects.create(name='book', author=self.author, city=self.city2)
            self.book.genres.set([genre1, genre2, genre3, genre4, genre5])

        for el in range(100):
            self.bookmark = Bookmark.objects.create(book=self.book, name='bookmark')

    def test_get_fields_data(self):
        data = get_relations(BookWithGenreSerializer)
        self.assertEqual(['author', 'city__parent_city'], data['select'])
        self.assertEqual(['genres__city__parent_city'], data['prefetch'])

    def test_optimize_queryset(self):
        reset_queries()
        _ = BookWithGenreSerializer(self.book).data
        self.assertEqual(len(connection.queries), 4)

    def test_simple_queryset(self):
        reset_queries()
        _ = BookWithGenreSerializer(self.book).data
        self.assertEqual(len(connection.queries), 4)

    def test_multiple_queryset(self):
        reset_queries()
        _ = BookWithGenreSerializer(Book.objects.all(), many=True).data
        self.assertEqual(len(connection.queries), 4)

    def test_multiple_queryset_by_list(self):
        reset_queries()
        _ = BookWithGenreSerializer(list(Book.objects.all()), many=True).data
        self.assertEqual(len(connection.queries), 5)

    def test_multiple_queryset_by_list_serializer(self):
        reset_queries()
        _ = BookWithGenreListSerializer(Book.objects.all(), many=True).data
        self.assertEqual(len(connection.queries), 4)

    def test_multiple_by_related_object_serializer(self):
        reset_queries()
        _ = BookmarkSerializer(Bookmark.objects.first()).data
        self.assertEqual(len(connection.queries), 5)

    def test_enable_and_disable_optimization(self):
        reset_queries()
        _ = BookmarkSerializer(Bookmark.objects.all(), many=True, optimize_queryset=False).data
        self.assertTrue(len(connection.queries) > 300)
        reset_queries()
        _ = BookWithGenreSerializer(Book.objects.first(), optimize_queryset=False).data
        self.assertTrue(len(connection.queries) > 10)
        reset_queries()
        _ = DisableOptimizationBookSerializer(Book.objects.all(), many=True).data
        self.assertTrue(len(connection.queries) > 300)
        reset_queries()
        _ = DisableOptimizationBookSerializer(Book.objects.all(), many=True, optimize_queryset=True).data
        self.assertTrue(len(connection.queries) < 10)


class TestDynamicSerializer(TestCase):
    def test_success_data(self):
        data = {'name': 'Mark', 'age': 13}
        serializer = AirDynamicSerializer(
            data=data, values={'name': serializers.CharField(), 'age': serializers.IntegerField()}
        )
        serializer.is_valid()
        self.assertEqual(len(serializer.errors), 0)

    def test_error_data(self):
        data = {'name': 'Mark', 'age': 'age'}
        serializer = AirDynamicSerializer(
            data=data, values={'name': serializers.CharField(), 'age': serializers.FloatField()}
        )
        serializer.is_valid()
        self.assertEqual(len(serializer.errors), 1)


class TestFilters(TestCase):
    def setUp(self) -> None:
        self.author1 = Author.objects.create(name='author')
        self.author2 = Author.objects.create(name='author')
        Book.objects.create(name='book1', author=self.author1)
        Book.objects.create(name='book2', author=self.author2)

    def test_multiple_filer(self):
        filters = AuthorFilter(queryset=Book.objects.all())
        self.assertEqual(len(filters.qs), 2)
        filters = AuthorFilter({'author': '1'}, queryset=Book.objects.all())
        self.assertEqual(len(filters.qs), 1)
        filters = AuthorFilter({'author': '   1, 2  '}, queryset=Book.objects.all())
        self.assertEqual(len(filters.qs), 2)


class TestDecoratorsSerializer(TestCase):
    @queries_count
    def test_queries_count(self):
        Book.objects.create(name='123')
        Book.objects.all().count()
