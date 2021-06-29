from rest_framework import serializers

from air_drf_relation.serializers import AirModelSerializer
from air_drf_relation.fields import RelatedField
from .models import Author, Book, City, Magazine


class AuthorSerializer(AirModelSerializer):
    class Meta:
        model = Author
        fields = ('id', 'name')


class CitySerializer(AirModelSerializer):
    class Meta:
        model = City
        fields = ('uuid', 'name')


class BookSerializer(AirModelSerializer):
    author = RelatedField(AuthorSerializer)
    city = RelatedField(CitySerializer, queryset_function_name='filter_city_by_active')

    def queryset_author(self, queryset):
        return queryset.filter(active=True)

    def filter_city_by_active(self, queryset):
        return queryset.filter(active=True)

    class Meta:
        model = Book
        fields = ('uuid', 'name', 'author', 'city')


class BookReadOnlySerializer(AirModelSerializer):
    author = RelatedField(AuthorSerializer, read_only=True)
    city = RelatedField(CitySerializer, read_only=True)

    class Meta:
        model = Book
        fields = ('uuid', 'name', 'author', 'city')


class BookHiddenSerializer(AirModelSerializer):
    author = RelatedField(AuthorSerializer, hidden=True)

    class Meta:
        model = Book
        fields = ('uuid', 'name', 'author', 'city')
        extra_kwargs = {
            'name': {'hidden': True}
        }


class BookActionKwargsSerializer(AirModelSerializer):
    author = RelatedField(AuthorSerializer)
    city = RelatedField(CitySerializer)

    class Meta:
        model = Book
        fields = ('uuid', 'name', 'author', 'city')
        action_extra_kwargs = {
            'create': {'city': {'hidden': True}},
            'second_create': {'author': {'read_only': True}, 'name': {'hidden': True}},
        }


class DefaultBookSerializer(AirModelSerializer):
    class Meta:
        model = Book
        fields = ('uuid', 'name', 'author', 'city')


class MagazineSerializer(AirModelSerializer):
    author = RelatedField(AuthorSerializer)
    city = RelatedField(CitySerializer)

    class Meta:
        model = Magazine
        fields = ('id', 'name', 'author', 'city')


class MagazineSpecialSerializer(AirModelSerializer):
    city = RelatedField(CitySerializer)

    class Meta:
        model = Magazine
        fields = ('id', 'name', 'author', 'city')

    def queryset_author(self, queryset):
        return queryset.filter(active=True)
