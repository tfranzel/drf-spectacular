import tempfile
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.urls import reverse
from rest_framework import serializers, viewsets
from rest_framework.routers import SimpleRouter
from rest_framework.test import APIClient

from drf_spectacular.generators import SchemaGenerator
from tests import assert_schema

fs = FileSystemStorage(location=tempfile.gettempdir())


class Aux(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    field_foreign = models.ForeignKey('Aux', null=True, on_delete=models.CASCADE)


class AllFields(models.Model):
    # basics
    field_int = models.IntegerField()
    field_float = models.FloatField()
    field_bool = models.BooleanField()
    field_char = models.CharField(max_length=100)
    field_text = models.TextField()
    # special
    field_slug = models.SlugField()
    field_email = models.EmailField()
    field_uuid = models.UUIDField()
    field_url = models.URLField()
    if models.IPAddressField in serializers.ModelSerializer.serializer_field_mapping:
        field_ip = models.IPAddressField()
    else:
        field_ip = models.GenericIPAddressField(protocol='ipv6')
    field_ip_generic = models.GenericIPAddressField(protocol='ipv6')
    field_decimal = models.DecimalField(max_digits=6, decimal_places=3)
    field_file = models.FileField(storage=fs)
    field_img = models.ImageField(storage=fs)
    field_date = models.DateField()
    field_datetime = models.DateTimeField()
    field_bigint = models.BigIntegerField()
    field_smallint = models.SmallIntegerField()
    field_posint = models.PositiveIntegerField()
    field_possmallint = models.PositiveSmallIntegerField()
    field_nullbool = models.NullBooleanField()
    field_time = models.TimeField()
    field_duration = models.DurationField()

    # relations
    field_foreign = models.ForeignKey(Aux, on_delete=models.CASCADE, help_text='main aux object')
    field_m2m = models.ManyToManyField(Aux, help_text='set of related aux objects')
    field_o2o = models.OneToOneField(Aux, on_delete=models.CASCADE, help_text='bound aux object')
    # overrides
    field_regex = models.CharField(max_length=50)
    field_bool_override = models.BooleanField()

    @property
    def field_model_property_float(self) -> float:
        return 1.337

    @property
    def field_list(self):
        return [1.1, 2.2, 3.3]

    def model_function_basic(self) -> bool:
        return True

    def model_function_model(self) -> Aux:
        return self.field_foreign


class AllFieldsSerializer(serializers.ModelSerializer):
    field_decimal_uncoerced = serializers.DecimalField(
        source='field_decimal',
        max_digits=6,
        decimal_places=3,
        coerce_to_string=False
    )
    field_method_float = serializers.SerializerMethodField()

    def get_field_method_float(self, obj) -> float:
        return 1.3456

    field_method_object = serializers.SerializerMethodField()

    def get_field_method_object(self, obj) -> dict:
        return {'key': 'value'}

    field_regex = serializers.RegexField(r'^[a-zA-z0-9]{10}\-[a-z]')

    # composite fields
    field_list = serializers.ListField(
        child=serializers.FloatField(), min_length=3, max_length=100,
    )

    # extra related fields
    field_related_slug = serializers.SlugRelatedField(
        read_only=True, source='field_foreign', slug_field='id'
    )
    field_related_string = serializers.StringRelatedField(
        source='field_foreign'
    )
    field_related_hyperlink = serializers.HyperlinkedRelatedField(
        read_only=True, source='field_foreign', view_name='aux-detail'
    )
    field_identity_hyperlink = serializers.HyperlinkedIdentityField(
        read_only=True, view_name='allfields-detail'
    )

    # read only - model traversal
    field_read_only_nav_uuid = serializers.ReadOnlyField(source='field_foreign.id')
    field_read_only_nav_uuid_3steps = serializers.ReadOnlyField(
        source='field_foreign.field_foreign.field_foreign.id',
        allow_null=True,  # force field output even if traversal fails
    )
    field_read_only_model_function_basic = serializers.ReadOnlyField(source='model_function_basic')
    field_read_only_model_function_model = serializers.ReadOnlyField(source='model_function_model.id')

    # override default writable bool field with readonly
    field_bool_override = serializers.ReadOnlyField()

    field_model_property_float = serializers.ReadOnlyField()

    class Meta:
        fields = '__all__'
        model = AllFields


class AuxSerializer(serializers.ModelSerializer):
    """ description for aux object """
    class Meta:
        fields = '__all__'
        model = Aux


class AllFieldsModelViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = AllFieldsSerializer
    queryset = AllFields.objects.all()

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class AuxModelViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuxSerializer
    queryset = Aux.objects.all()


router = SimpleRouter()
router.register('allfields', AllFieldsModelViewset)
router.register('aux', AuxModelViewset)
urlpatterns = router.urls


@pytest.mark.urls(__name__)
def test_fields(no_warnings):
    from django.core.validators import URLValidator

    generator = SchemaGenerator()
    schema = generator.get_schema(request=None, public=True)

    # url pattern changed between django 3.0 and 3.1
    field_url = schema['components']['schemas']['AllFields']['properties']['field_url']
    assert field_url['pattern'] == URLValidator.regex.pattern
    field_url['pattern'] = 'URL_REGEX_PATTERN'

    assert_schema(schema, 'tests/test_fields.yml')


@pytest.mark.urls(__name__)
@pytest.mark.django_db
def test_model_setup_is_valid():
    aux = Aux()
    aux.save()

    m = AllFields(
        # basics
        field_int=1,
        field_float=1.25,
        field_bool=True,
        field_char='char',
        field_text='text',
        # special
        field_slug='all_fields',
        field_email='test@example.com',
        field_uuid='00000000-00000000-00000000-00000000',
        field_url='https://github.com/tfranzel/drf-spectacular',
        field_ip='127.0.0.1',
        field_ip_generic='2001:db8::8a2e:370:7334',
        field_decimal=Decimal('666.333'),
        field_file=None,
        field_img=None,  # TODO fill with data below
        field_date=date.today(),
        field_datetime=datetime.now(),
        field_bigint=11111111111111,
        field_smallint=111111,
        field_posint=123,
        field_possmallint=1,
        field_nullbool=None,
        field_time='00:05:23.283',
        field_duration=timedelta(seconds=10),
        # relations
        field_foreign=aux,
        field_o2o=aux,
        # overrides
        field_regex='12345asdfg-a',
        field_bool_override=True,
    )
    m.field_file.save('hello.txt', ContentFile("hello world"), save=True)
    m.save()
    m.field_m2m.add(aux)

    response = APIClient().get(reverse('allfields-detail', args=(m.pk,)))
    assert response.status_code == 200
