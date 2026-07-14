import pytest
from django.db import models
from django.urls import include, re_path
from rest_framework import serializers, viewsets
from rest_framework.routers import SimpleRouter

from tests import assert_schema, generate_schema


class Book(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)

class BookSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Book
        fields = ('name',)

def _generate_simple_router_schema(viewset):
    router = SimpleRouter()
    router.register('books', viewset, basename='books')
    urlpatterns = [
        re_path('', include(router.urls)),
    ]
    return generate_schema(None, patterns=urlpatterns)

@pytest.mark.contrib('rest_framework_lookup_value')
def test_drf_lookup_value_regex_integer(no_warnings):
    class BookViewSet(viewsets.ModelViewSet):
        queryset = Book.objects.all()
        serializer_class = BookSerializer
        lookup_field = 'id'
        lookup_value_regex = r'\d+'

    assert_schema(
        _generate_simple_router_schema(BookViewSet),
        'tests/contrib/test_drf_lookup_value.yml',
    )
