import uuid
from datetime import datetime, date
from decimal import Decimal
from unittest import mock

import pytest
from django.core.files.base import ContentFile
from django.db import models
from rest_framework import serializers, viewsets, routers
from rest_framework.renderers import JSONRenderer

from drf_spectacular.openapi import SchemaGenerator, AutoSchema
from tests import assert_schema


# TODO Fields known to DRF and mapping
# models.BigIntegerField: IntegerField,
# models.CommaSeparatedIntegerField: CharField,
# models.Field: ModelField,
# models.ImageField: ImageField,
# models.NullBooleanField: NullBooleanField,
# models.PositiveIntegerField: IntegerField,
# models.PositiveSmallIntegerField: IntegerField,
# models.SmallIntegerField: IntegerField,
# models.TimeField: TimeField,
# models.FilePathField: FilePathField,


class Aux(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


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
    field_ip = models.IPAddressField()
    field_ip_generic = models.GenericIPAddressField(protocol='ipv6')
    field_decimal = models.DecimalField(max_digits=6, decimal_places=3)
    field_file = models.FileField()
    field_img = models.ImageField()
    field_date = models.DateField()
    field_datetime = models.DateTimeField()
    field_bigint = models.BigIntegerField()
    field_smallint = models.SmallIntegerField()
    # relations
    field_foreign = models.ForeignKey(Aux, on_delete=models.CASCADE)
    field_m2m = models.ManyToManyField(Aux)
    field_o2o = models.OneToOneField(Aux, on_delete=models.CASCADE)


class AllFieldsSerializer(serializers.ModelSerializer):
    field_method_float = serializers.SerializerMethodField()
    field_method_object = serializers.SerializerMethodField()

    def get_field_method_float(self, obj) -> float:
        return 0

    def get_field_method_object(self, obj) -> dict:
        return {'key': 'value'}

    class Meta:
        fields = '__all__'
        model = AllFields


class AlbumModelViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = AllFieldsSerializer
    queryset = AllFields.objects.none()

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


@mock.patch('rest_framework.settings.api_settings.DEFAULT_SCHEMA_CLASS', AutoSchema)
def test_fields():
    router = routers.SimpleRouter()
    router.register('allfields', AlbumModelViewset, basename="allfields")
    generator = SchemaGenerator(patterns=router.urls)
    schema = generator.get_schema(request=None, public=True)

    assert_schema(schema, 'tests/test_fields.yml')


@pytest.mark.django_db
def test_model_setup_is_valid():
    a = Aux()
    a.save()

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
        # relations
        field_foreign=a,
        field_o2o=a,
    )
    m.field_file.save('hello.txt', ContentFile("hello world"), save=True)
    m.save()
    m.field_m2m.add(a)

    JSONRenderer().render(
        AllFieldsSerializer(m).data,
        accepted_media_type='application/json; indent=4'
    ).decode()
