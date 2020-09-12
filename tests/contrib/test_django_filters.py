import pytest
from django.db import models
from django.urls import path
from rest_framework import generics, serializers
from rest_framework.test import APIClient

from drf_spectacular.contrib.django_filters import DjangoFilterBackend
from tests import assert_schema, generate_schema

try:
    from django_filters.rest_framework import FilterSet, NumberFilter
except ImportError:
    class FilterSet:
        pass

    class NumberFilter:
        pass


class Product(models.Model):
    category = models.CharField(max_length=10, choices=(('A', 'aaa'), ('B', 'b')))
    in_stock = models.BooleanField()
    price = models.FloatField()


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class ProductFilter(FilterSet):
    min_price = NumberFilter(field_name="price", lookup_expr='gte')
    max_price = NumberFilter(field_name="price", lookup_expr='lte')

    class Meta:
        model = Product
        fields = ['category', 'in_stock', 'min_price', 'max_price']


class ProductList(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ProductFilter


@pytest.mark.contrib('django_filter')
def test_django_filters(no_warnings):
    assert_schema(
        generate_schema('products', view=ProductList),
        'tests/contrib/test_django_filters.yml'
    )


urlpatterns = [
    path('api/products/', ProductList.as_view()),
]


@pytest.mark.urls(__name__)
@pytest.mark.django_db
def test_django_filters_requests(no_warnings):
    Product.objects.create(category='X', price=4, in_stock=True)

    response = APIClient().get('/api/products/?min_price=3')
    assert response.status_code == 200
    assert len(response.json()) == 1
    response = APIClient().get('/api/products/?min_price=5')
    assert response.status_code == 200
    assert len(response.json()) == 0
