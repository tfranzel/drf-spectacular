from unittest import mock

import pytest
from django.db import models
from polymorphic.models import PolymorphicModel
from rest_framework import viewsets, serializers, routers
from rest_framework.renderers import JSONRenderer
from rest_polymorphic.serializers import PolymorphicSerializer

from drf_spectacular.contrib.rest_polymorphic import PolymorphicAutoSchema
from drf_spectacular.openapi import SchemaGenerator
from tests import assert_schema, lazy_serializer


class Person(PolymorphicModel):
    address = models.CharField(max_length=30)


class LegalPerson(Person):
    company_name = models.CharField(max_length=30)
    board = models.ManyToManyField('Person', blank=True, null=True)


class NaturalPerson(Person):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)


class PersonSerializer(PolymorphicSerializer):
    model_serializer_mapping = {
        LegalPerson: lazy_serializer('tests.test_polymorphic.LegalPersonSerializer'),
        NaturalPerson: lazy_serializer('tests.test_polymorphic.NaturalPersonSerializer'),
    }


class LegalPersonSerializer(serializers.ModelSerializer):
    board = PersonSerializer(many=True, read_only=True)

    class Meta:
        model = LegalPerson
        fields = ('company_name', 'address', 'board')


class NaturalPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = NaturalPerson
        fields = ('first_name', 'last_name', 'address')


class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


@mock.patch('rest_framework.settings.api_settings.DEFAULT_SCHEMA_CLASS', PolymorphicAutoSchema)
def test_polymorphic():
    router = routers.SimpleRouter()
    router.register('persons', PersonViewSet, basename="person")
    generator = SchemaGenerator(patterns=router.urls)
    schema = generator.get_schema(request=None, public=True)

    assert_schema(schema, 'tests/test_polymorphic.yml')


@pytest.mark.django_db
def test_model_setup_is_valid():
    natural = NaturalPerson(first_name='asd', last_name='xx')
    natural.save()
    legal = LegalPerson(company_name='xxx', address='asd')
    legal.save()
    legal.board.add(natural)

    output = JSONRenderer().render(
        PersonSerializer(legal).data,
        accepted_media_type='application/json; indent=4'
    ).decode()
    print(output)
