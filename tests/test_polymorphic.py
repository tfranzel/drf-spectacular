from unittest import mock

from django.db import models
from rest_framework import viewsets, serializers
from rest_framework.response import Response

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema, PolymorphicProxySerializer
from tests import assert_schema, generate_schema


class LegalPerson2(models.Model):
    company_name = models.CharField(max_length=30)


class NaturalPerson2(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)


class LegalPersonSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = LegalPerson2
        fields = ('id', 'company_name', 'type')

    def get_type(self, obj) -> str:
        return 'legal'


class NaturalPersonSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = NaturalPerson2
        fields = ('id', 'first_name', 'last_name', 'type')

    def get_type(self, obj) -> str:
        return 'natural'


with mock.patch('rest_framework.settings.api_settings.DEFAULT_SCHEMA_CLASS', AutoSchema):
    class PersonViewSet(viewsets.GenericViewSet):
        @extend_schema(
            request=PolymorphicProxySerializer(
                component_name='MetaPerson',
                serializers=[LegalPersonSerializer, NaturalPersonSerializer],
                resource_type_field_name='type',
            ),
            responses=PolymorphicProxySerializer(
                component_name='MetaPerson',
                serializers=[LegalPersonSerializer, NaturalPersonSerializer],
                resource_type_field_name='type',
            )
        )
        def create(self, request, *args, **kwargs):
            return Response({})  # pragma: no cover


def test_polymorphic(no_warnings):
    assert_schema(
        generate_schema('persons', PersonViewSet),
        'tests/test_polymorphic.yml'
    )
