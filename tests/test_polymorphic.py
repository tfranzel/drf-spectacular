from unittest import mock

import pytest
from django.db import models
from rest_framework import serializers, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import (
    OpenApiParameter, PolymorphicProxySerializer, extend_schema, extend_schema_field,
)
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

        @extend_schema(
            request=implicit_poly_proxy,
            responses=implicit_poly_proxy,
            parameters=[OpenApiParameter('id', int, OpenApiParameter.PATH)],
        )
        def partial_update(self, request, *args, **kwargs):
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

        @extend_schema(
            request=explicit_poly_proxy,
            responses=explicit_poly_proxy,
            parameters=[OpenApiParameter('id', int, OpenApiParameter.PATH)],
        )
        def partial_update(self, request, *args, **kwargs):
            return Response({})  # pragma: no cover


@pytest.mark.parametrize('viewset', [ImplicitPersonViewSet, ExplicitPersonViewSet])
def test_polymorphic(no_warnings, viewset):
    assert_schema(
        generate_schema('persons', viewset),
        'tests/test_polymorphic.yml'
    )


def test_polymorphic_serializer_as_field_via_extend_schema_field(no_warnings):
    @extend_schema_field(
        PolymorphicProxySerializer(
            component_name='MetaPerson',
            serializers=[LegalPersonSerializer, NaturalPersonSerializer],
            resource_type_field_name='type',
        )
    )
    class XField(serializers.DictField):
        pass  # pragma: no cover

    class XSerializer(serializers.Serializer):
        field = XField()

    @extend_schema(request=XSerializer, responses=XSerializer)
    @api_view(['GET'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('x', view_function=view_func)
    assert 'MetaPerson' in schema['components']['schemas']
    assert 'MetaPerson' in schema['components']['schemas']['X']['properties']['field']['$ref']


def test_polymorphic_serializer_as_method_field_via_extend_schema_field(no_warnings):
    class XSerializer(serializers.Serializer):
        field = serializers.SerializerMethodField()

        @extend_schema_field(
            PolymorphicProxySerializer(
                component_name='MetaPerson',
                serializers=[LegalPersonSerializer, NaturalPersonSerializer],
                resource_type_field_name='type',
            )
        )
        def get_field(self, request):
            pass  # pragma: no cover

    @extend_schema(request=XSerializer, responses=XSerializer)
    @api_view(['GET'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('x', view_function=view_func)
    assert 'MetaPerson' in schema['components']['schemas']
    assert schema['components']['schemas']['X'] == {
        'type': 'object',
        'properties': {
            'field': {'allOf': [{'$ref': '#/components/schemas/MetaPerson'}], 'readOnly': True}
        },
        'required': ['field']
    }


def test_stripped_down_polymorphic_serializer(no_warnings):
    @extend_schema_field(
        PolymorphicProxySerializer(
            component_name='MetaPerson',
            serializers=[LegalPersonSerializer, NaturalPersonSerializer],
            resource_type_field_name=None,
        )
    )
    class XField(serializers.DictField):
        pass  # pragma: no cover

    class XSerializer(serializers.Serializer):
        field = XField()

    @extend_schema(request=XSerializer, responses=XSerializer)
    @api_view(['GET'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('x', view_function=view_func)
    assert schema['components']['schemas']['MetaPerson'] == {'oneOf': [
        {'$ref': '#/components/schemas/LegalPerson'},
        {'$ref': '#/components/schemas/NaturalPerson'}
    ]}
