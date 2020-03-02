from unittest import mock

from django.db import models
from polymorphic.models import PolymorphicModel
from rest_framework import viewsets, serializers, routers
from rest_polymorphic.serializers import PolymorphicSerializer

from drf_spectacular.contrib.rest_polymorphic import PolymorphicAutoSchema
from drf_spectacular.openapi import SchemaGenerator
from tests import dump


class Person(PolymorphicModel):
    address = models.CharField(max_length=30)


class LegalPerson(Person):
    company_name = models.CharField(max_length=30)


class NaturalPerson(Person):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)


class LegalPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalPerson
        fields = ('company_name', 'address')


class NaturalPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = NaturalPerson
        fields = ('first_name', 'last_name', 'address')


class PersonSerializer(PolymorphicSerializer):
    model_serializer_mapping = {
        LegalPerson: LegalPersonSerializer,
        NaturalPerson: NaturalPersonSerializer
    }


class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


@mock.patch('rest_framework.settings.api_settings.DEFAULT_SCHEMA_CLASS', PolymorphicAutoSchema)
def test_polymorphic():
    router = routers.SimpleRouter()
    router.register('persons', PersonViewSet, basename="person")
    generator = SchemaGenerator(patterns=router.urls)
    schema = generator.get_schema(request=None, public=True)

    with open('tests/test_polymorphic.yml', 'rb') as fh:
        assert dump(schema) == fh.read()
