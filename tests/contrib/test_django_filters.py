import uuid

import pytest
from django.db import models
from django.db.models import F
from django.urls import include, path
from rest_framework import routers, serializers, viewsets
from rest_framework.test import APIClient

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_field
from tests import assert_schema, generate_schema

try:
    from django_filters.rest_framework import (
        AllValuesFilter, BaseInFilter, BooleanFilter, CharFilter, DjangoFilterBackend, FilterSet,
        ModelChoiceFilter, ModelMultipleChoiceFilter, MultipleChoiceFilter, NumberFilter,
        NumericRangeFilter, OrderingFilter, RangeFilter, UUIDFilter,
    )
except ImportError:
    class DjangoFilterBackend:  # type: ignore
        pass

    class FilterSet:  # type: ignore
        pass

    class NumberFilter:  # type: ignore
        def init(self, **kwargs):
            pass

    CharFilter = NumberFilter
    OrderingFilter = NumberFilter
    BaseInFilter = NumberFilter
    BooleanFilter = NumberFilter
    UUIDFilter = NumberFilter
    NumericRangeFilter = NumberFilter
    RangeFilter = NumberFilter
    MultipleChoiceFilter = NumberFilter
    ModelChoiceFilter = NumberFilter
    ModelMultipleChoiceFilter = NumberFilter
    AllValuesFilter = NumberFilter


class OtherSubProduct(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)


class Product(models.Model):
    category = models.CharField(
        max_length=10,
        choices=(('A', 'aaa'), ('B', 'b')),
        help_text='some category description'
    )
    in_stock = models.BooleanField()
    price = models.FloatField()
    other_sub_product = models.ForeignKey(OtherSubProduct, on_delete=models.CASCADE)


class SubProduct(models.Model):
    sub_price = models.FloatField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


def external_filter_method(queryset, name, value):
    return queryset  # pragma: no cover


class CustomBooleanFilter(BooleanFilter):
    pass


class CustomBaseInFilter(BaseInFilter):
    pass


class ProductFilter(FilterSet):
    # explicit filter declaration
    max_price = NumberFilter(field_name="price", lookup_expr='lte', label='highest price')
    max_sub_price = NumberFilter(field_name="subproduct__sub_price", lookup_expr='lte')
    sub = NumberFilter(field_name="subproduct", lookup_expr='exact')
    int_id = NumberFilter(method='filter_method_typed')
    number_id = NumberFilter(method='filter_method_untyped', help_text='some injected help text')
    number_id_ext = NumberFilter(method=external_filter_method)
    # implicit filter declaration
    subproduct__sub_price = NumberFilter()  # reverse relation
    other_sub_product__uuid = UUIDFilter()  # forward relation
    # special cases
    ordering = OrderingFilter(
        fields=('price', 'in_stock'),
        field_labels={'price': 'Price', 'in_stock': 'in stock'},
    )
    in_categories = BaseInFilter(field_name='category')
    is_free = BooleanFilter(field_name='price', lookup_expr='isnull')
    price_range = RangeFilter(field_name='price')
    model_multi_cat = ModelMultipleChoiceFilter(field_name='category', queryset=Product.objects.all())
    model_single_cat = ModelChoiceFilter(field_name='category', queryset=Product.objects.all())
    all_values = AllValuesFilter(field_name='price')

    custom_filter = CustomBooleanFilter(field_name='price', lookup_expr='isnull')
    custom_underspec_filter = CustomBaseInFilter(field_name='category')

    model_multi_cat_relation = ModelMultipleChoiceFilter(
        field_name='other_sub_product',
        queryset=OtherSubProduct.objects.all()
    )

    price_range_vat = RangeFilter(field_name='price_vat')
    price_range_vat_decorated = extend_schema_field(OpenApiTypes.INT)(
        RangeFilter(field_name='price_vat')
    )

    class Meta:
        model = Product
        fields = [
            'category', 'in_stock', 'max_price', 'max_sub_price', 'sub',
            'subproduct__sub_price', 'other_sub_product__uuid',
        ]

    def filter_method_typed(self, queryset, name, value: int):
        return queryset.filter(id=int(value))

    def filter_method_untyped(self, queryset, name, value):
        return queryset.filter(id=int(value))  # pragma: no cover


@extend_schema(
    examples=[
        OpenApiExample('Magic example 1', value='1337', parameter_only=('max_price', 'query')),
        OpenApiExample('Magic example 2', value='1234', parameter_only=('max_price', 'query')),
    ]
)
class ProductViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ProductFilter

    def get_queryset(self):
        return Product.objects.all().annotate(
            price_vat=F('price') * 1.19
        )


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
@pytest.mark.contrib('django_filter')
def test_django_filters_requests(no_warnings):
    other_sub_product = OtherSubProduct.objects.create(uuid=uuid.uuid4())
    product = Product.objects.create(
        category='A', price=4, in_stock=True, other_sub_product=other_sub_product
    )
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
    response = APIClient().get(f'/api/products/?int_id={product.id}')
    assert response.status_code == 200
    assert len(response.json()) == 1
    response = APIClient().get(f'/api/products/?int_id={product.id + 1}')
    assert response.status_code == 200
    assert len(response.json()) == 0
    response = APIClient().get('/api/products/?ordering=in_stock,-price')
    assert response.status_code == 200
    assert len(response.json()) == 1
    response = APIClient().get('/api/products/?price_range_min=7')
    assert response.status_code == 200
    assert len(response.json()) == 0
    response = APIClient().get('/api/products/?price_range_max=1')
    assert response.status_code == 200
    assert len(response.json()) == 0
    response = APIClient().get('/api/products/?price_range_min=1&price_range_max=5')
    assert response.status_code == 200
    assert len(response.json()) == 1
    response = APIClient().get('/api/products/?multi_cat=A&multi_cat=B')
    assert response.status_code == 200, response.content
    assert len(response.json()) == 1


def test_through_model_multi_choice_filter(no_warnings):
    class RelationModel(models.Model):
        test = models.CharField(max_length=50)

    class TestModel(models.Model):
        reltd = models.ManyToManyField(RelationModel, through="ThroughModel")

    class ThroughModel(models.Model):
        tm = models.ForeignKey(TestModel, on_delete=models.PROTECT)
        rm = models.ForeignKey(RelationModel, on_delete=models.PROTECT)

    class MyFilter(FilterSet):
        reltd = ModelMultipleChoiceFilter(field_name="reltd", label="reltd")

        class Meta:
            model = TestModel
            fields = ["reltd"]

    class TestSerializer(serializers.ModelSerializer):
        class Meta:
            model = TestModel
            fields = '__all__'

    class TestViewSet(viewsets.ModelViewSet):
        queryset = TestModel.objects.all()
        serializer_class = TestSerializer

        filter_backends = [DjangoFilterBackend]
        filterset_class = MyFilter

    generate_schema('x', TestViewSet)


def test_boolean_filter_subclassing_in_different_import_path(no_warnings):
    # this import is important as there is a override via subclassing
    # happening in django_filter.rest_framework.filters
    import django_filters

    class DjangoFilterDummyModel(models.Model):
        seen = models.DateTimeField(null=True)

    class XSerializer(serializers.ModelSerializer):
        class Meta:
            model = DjangoFilterDummyModel
            fields = "__all__"

    class XFilterSet(FilterSet):
        class Meta:
            model = DjangoFilterDummyModel
            fields = []

        seen = django_filters.BooleanFilter(field_name="seen", lookup_expr="isnull")

    class XViewSet(viewsets.ModelViewSet):
        queryset = DjangoFilterDummyModel.objects.all()
        serializer_class = XSerializer
        filterset_class = XFilterSet
        filter_backends = [DjangoFilterBackend]

    schema = generate_schema('/x', XViewSet)
    assert schema['paths']['/x/']['get']['parameters'] == [
        {'in': 'query', 'name': 'seen', 'schema': {'type': 'boolean'}}
    ]
