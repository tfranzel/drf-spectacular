import uuid
from datetime import datetime, date
from decimal import Decimal
from unittest import mock

import pytest
from django.core.files.base import ContentFile
from django.db import models
from rest_framework import serializers, viewsets
from rest_framework.renderers import JSONRenderer

from drf_spectacular.openapi import AutoSchema
from tests import assert_schema, generate_schema, skip_on_travis


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
    # overrides
    field_regex = models.CharField(max_length=50)
    field_bool_override = models.BooleanField()

    @property
    def field_model_property_float(self) -> float:
        return 1.337


class AllFieldsSerializer(serializers.ModelSerializer):
    field_method_float = serializers.SerializerMethodField()
    field_method_object = serializers.SerializerMethodField()

    field_regex = serializers.RegexField(r'^[a-zA-z0-9]{10}\-[a-z]')

    # read only - model traversal
    field_read_only_nav_uuid = serializers.ReadOnlyField(source='field_foreign.id')
    field_read_only_nav_uuid_3steps = serializers.ReadOnlyField(
        source='field_foreign.field_foreign.field_foreign.id',
        allow_null=True,  # force field output even if traversal fails
    )
    # override default writable bool field with readonly
    field_bool_override = serializers.ReadOnlyField()

    field_model_property_float = serializers.ReadOnlyField()

    def get_field_method_float(self, obj) -> float:
        return 1.3456

    def get_field_method_object(self, obj) -> dict:
        return {'key': 'value'}

    class Meta:
        fields = '__all__'
        model = AllFields


class AllFieldsModelViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = AllFieldsSerializer
    queryset = AllFields.objects.none()

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


@mock.patch('rest_framework.settings.api_settings.DEFAULT_SCHEMA_CLASS', AutoSchema)
def test_fields(no_warnings):
    assert_schema(
        generate_schema('allfields', AllFieldsModelViewset),
        'tests/test_fields.yml'
    )


@skip_on_travis
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

    output = JSONRenderer().render(
        AllFieldsSerializer(m).data,
        accepted_media_type='application/json; indent=4'
    ).decode()
    print(output)
