import pytest
from django.db import models
from django.urls import include, path
from rest_framework import routers, serializers, viewsets
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


class SubProduct(models.Model):
    sub_price = models.FloatField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class ProductFilter(FilterSet):
    max_price = NumberFilter(field_name="price", lookup_expr='lte')
    max_sub_price = NumberFilter(field_name="subproduct__sub_price", lookup_expr='lte')
    sub = NumberFilter(field_name="subproduct", lookup_expr='exact')

    class Meta:
        model = Product
        fields = ['category', 'in_stock', 'max_price']


class ProductViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ProductFilter


@pytest.mark.contrib('django_filter')
def test_django_filters(no_warnings):
    assert_schema(
        generate_schema('products', ProductViewset),
        'tests/contrib/test_django_filters.yml'
    )


router = routers.SimpleRouter()
router.register('products', ProductViewset)
urlpatterns = [
    path('api/', include(router.urls)),
]


@pytest.mark.urls(__name__)
@pytest.mark.django_db
def test_django_filters_requests(no_warnings):
    product = Product.objects.create(category='X', price=4, in_stock=True)
    SubProduct.objects.create(sub_price=5, product=product)

    response = APIClient().get('/api/products/?max_price=1')
    assert response.status_code == 200
    assert len(response.json()) == 0
    response = APIClient().get('/api/products/?max_price=5')
    assert response.status_code == 200
    assert len(response.json()) == 1
    response = APIClient().get('/api/products/?max_sub_price=1')
    assert response.status_code == 200
    assert len(response.json()) == 0
    response = APIClient().get('/api/products/?max_sub_price=6')
    assert response.status_code == 200
    assert len(response.json()) == 1
    response = APIClient().get('/api/products/?sub=1')
    assert response.status_code == 200
    assert len(response.json()) == 1
    response = APIClient().get('/api/products/?sub=2')
    assert response.status_code == 200
    assert len(response.json()) == 0
