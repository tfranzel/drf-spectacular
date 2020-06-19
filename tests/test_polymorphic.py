from unittest import mock

import pytest
from django.db import models
from rest_framework import serializers, viewsets
from rest_framework.response import Response

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema
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
    implicit_poly_proxy = PolymorphicProxySerializer(
        component_name='MetaPerson',
        serializers=[LegalPersonSerializer, NaturalPersonSerializer],
        resource_type_field_name='type',
    )

    class ImplicitPersonViewSet(viewsets.GenericViewSet):
        @extend_schema(request=implicit_poly_proxy, responses=implicit_poly_proxy)
        def create(self, request, *args, **kwargs):
            return Response({})  # pragma: no cover

    explicit_poly_proxy = PolymorphicProxySerializer(
        component_name='MetaPerson',
        serializers={
            'legal': LegalPersonSerializer,
            'natural': NaturalPersonSerializer,
        },
        resource_type_field_name='type',
    )

    class ExplicitPersonViewSet(viewsets.GenericViewSet):
        @extend_schema(request=explicit_poly_proxy, responses=explicit_poly_proxy)
        def create(self, request, *args, **kwargs):
            return Response({})  # pragma: no cover


@pytest.mark.parametrize('viewset', [ImplicitPersonViewSet, ExplicitPersonViewSet])
def test_polymorphic(no_warnings, viewset):
    assert_schema(
        generate_schema('persons', viewset),
        'tests/test_polymorphic.yml'
    )
