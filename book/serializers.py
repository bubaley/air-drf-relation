from air_drf_relation.fields import AirRelatedField
from air_drf_relation.serializers import AirModelSerializer

from .models import Author, Book, Bookmark, City, Genre, Magazine


class AuthorSerializer(AirModelSerializer):
    class Meta:
        model = Author
        fields = ('id', 'name')


class ParentCitySerializer(AirModelSerializer):
    class Meta:
        model = City
        fields = ('uuid', 'name')


class CitySerializer(AirModelSerializer):
    parent_city = AirRelatedField(ParentCitySerializer, read_only=True)

    class Meta:
        model = City
        fields = ('uuid', 'name', 'parent_city')


class BookSerializer(AirModelSerializer):
    author = AirRelatedField(AuthorSerializer)
    city = AirRelatedField(CitySerializer, queryset_function_name='filter_city_by_active')

    def queryset_author(self, queryset):
        return queryset.filter(active=True)

    def filter_city_by_active(self, queryset):
        return queryset.filter(active=True)

    class Meta:
        model = Book
        fields = ('uuid', 'name', 'author', 'city')


class BookReadOnlySerializer(AirModelSerializer):
    author = AirRelatedField(AuthorSerializer, read_only=True)
    city = AirRelatedField(CitySerializer, read_only=True)

    class Meta:
        model = Book
        fields = ('uuid', 'name', 'author', 'city')


class BookHiddenSerializer(AirModelSerializer):
    author = AirRelatedField(AuthorSerializer, hidden=True)

    class Meta:
        model = Book
        fields = ('uuid', 'name', 'author', 'city')
        extra_kwargs = {'name': {'hidden': True}}


class BookActionKwargsSerializer(AirModelSerializer):
    author = AirRelatedField(AuthorSerializer)
    city = AirRelatedField(CitySerializer)

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
    author = AirRelatedField(AuthorSerializer)
    city = AirRelatedField(CitySerializer)

    class Meta:
        model = Magazine
        fields = ('id', 'name', 'author', 'city')


class DefaultMagazineSerializer(AirModelSerializer):
    class Meta:
        model = Magazine
        fields = ('id', 'name', 'author', 'city', 'available_cities')


class MagazineSpecialSerializer(AirModelSerializer):
    city = AirRelatedField(CitySerializer)

    class Meta:
        model = Magazine
        fields = ('id', 'name', 'author', 'city')

    def queryset_author(self, queryset):
        return queryset.filter(active=True)


class CityWritablePkSerializer(AirModelSerializer):
    class Meta:
        model = City
        fields = ('uuid', 'name')
        read_only_fields = ('uuid',)
        action_extra_kwargs = {'create,second_action': {'uuid': {'read_only': False}}, '_': {'name': {'hidden': True}}}


class GenreSerializer(AirModelSerializer):
    city = AirRelatedField(CitySerializer, read_only=True)

    class Meta:
        model = Genre
        fields = ('id', 'name', 'city')


class BookWithGenreSerializer(AirModelSerializer):
    genres = AirRelatedField(GenreSerializer, many=True)
    author = AirRelatedField(AuthorSerializer, read_only=True)
    city = AirRelatedField(CitySerializer, read_only=True)

    class Meta:
        model = Book
        fields = ('id', 'genres', 'name', 'author', 'city')


class DisableOptimizationBookSerializer(BookWithGenreSerializer):
    class Meta(BookWithGenreSerializer.Meta):
        optimize_queryset = False


class BookWithGenreListSerializer(AirModelSerializer):
    genres = GenreSerializer(many=True)

    class Meta:
        model = Book
        fields = ('id', 'genres', 'name')


class BookmarkSerializer(AirModelSerializer):
    book = BookWithGenreListSerializer()

    class Meta:
        model = Bookmark
        fields = ('id', 'name', 'book')
