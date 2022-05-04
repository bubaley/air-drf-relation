from django_filters import rest_framework as filters

from air_drf_relation.filters import AirModelMultipleChoiceField
from book.models import Book, Author


class AuthorFilter(filters.FilterSet):
    author = AirModelMultipleChoiceField(queryset=Author.objects.all())

    class Meta:
        model = Book
        fields = ('author',)
