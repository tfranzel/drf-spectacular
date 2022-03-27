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
from tests import assert_schema, generate_schema, get_request_schema, get_response_schema


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


PROXY_SERIALIZER_PARAMS = {
    'component_name': 'MetaPerson',
    'serializers': [LegalPersonSerializer, NaturalPersonSerializer],
    'resource_type_field_name': 'type',
}


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


@pytest.mark.parametrize('explicit', [True, False])
def test_many_polymorphic_serializer_extend_schema(no_warnings, explicit):
    if explicit:
        proxy_serializer = serializers.ListSerializer(
            child=PolymorphicProxySerializer(**PROXY_SERIALIZER_PARAMS)
        )
    else:
        proxy_serializer = PolymorphicProxySerializer(**PROXY_SERIALIZER_PARAMS, many=True)

    @extend_schema(request=proxy_serializer, responses=proxy_serializer)
    @api_view(['POST'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('/x/', view_function=view_func)
    assert 'MetaPerson' in schema['components']['schemas']
    op = schema['paths']['/x/']['post']
    assert get_response_schema(op) == {
        'type': 'array',
        'items': {'$ref': '#/components/schemas/MetaPerson'}
    }
    assert get_request_schema(op) == {
        'type': 'array',
        'items': {'$ref': '#/components/schemas/MetaPerson'}
    }


@pytest.mark.parametrize('explicit', [True, False])
def test_many_polymorphic_proxy_serializer_extend_schema_field(no_warnings, explicit):
    if explicit:
        proxy_serializer = serializers.ListField(
            child=PolymorphicProxySerializer(**PROXY_SERIALIZER_PARAMS)
        )
    else:
        proxy_serializer = PolymorphicProxySerializer(**PROXY_SERIALIZER_PARAMS, many=True)

    @extend_schema_field(proxy_serializer)
    class XField(serializers.DictField):
        pass  # pragma: no cover

    class XSerializer(serializers.Serializer):
        field = XField()

    @extend_schema(request=XSerializer, responses=XSerializer)
    @api_view(['POST'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('/x/', view_function=view_func)
    assert 'MetaPerson' in schema['components']['schemas']
    assert schema['components']['schemas']['X'] == {
        'type': 'object',
        'properties': {
            'field': {'type': 'array', 'items': {'$ref': '#/components/schemas/MetaPerson'}}
        },
        'required': ['field']
    }
    op = schema['paths']['/x/']['post']
    assert get_request_schema(op) == {'$ref': '#/components/schemas/X'}
    assert get_response_schema(op) == {'$ref': '#/components/schemas/X'}


def test_polymorphic_proxy_serializer_misusage(no_warnings):
    with pytest.raises(AssertionError):
        PolymorphicProxySerializer(**PROXY_SERIALIZER_PARAMS).data

    with pytest.raises(AssertionError):
        PolymorphicProxySerializer(**PROXY_SERIALIZER_PARAMS).to_representation(None)

    with pytest.raises(AssertionError):
        PolymorphicProxySerializer(**PROXY_SERIALIZER_PARAMS).to_internal_value(None)


@mock.patch('drf_spectacular.settings.spectacular_settings.COMPONENT_SPLIT_REQUEST', True)
@pytest.mark.parametrize('explicit', [True, False])
def test_polymorphic_split_request_with_ro_serializer(no_warnings, explicit):
    class BasicPersonSerializer(serializers.ModelSerializer):
        type = serializers.SerializerMethodField()

        class Meta:
            model = NaturalPerson2
            fields = ('id', 'type')

        def get_type(self, obj) -> str:
            return 'basic'

    if explicit:
        poly_proxy = PolymorphicProxySerializer(
            component_name='MetaPerson',
            serializers={'natural': NaturalPersonSerializer, 'basic': BasicPersonSerializer},
            resource_type_field_name='type',
        )
    else:
        poly_proxy = PolymorphicProxySerializer(
            component_name='MetaPerson',
            serializers=[NaturalPersonSerializer, BasicPersonSerializer],
            resource_type_field_name='type',
        )

    @extend_schema(request=poly_proxy, responses=poly_proxy)
    @api_view(['POST'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('x', view_function=view_func)
    components = schema['components']['schemas']
    assert 'BasicPersonRequest' not in components
    assert components['MetaPerson']['oneOf'] == [
        {'$ref': '#/components/schemas/NaturalPerson'},
        {'$ref': '#/components/schemas/BasicPerson'}
    ]
    assert components['MetaPerson']['discriminator']['mapping'] == {
        'natural': '#/components/schemas/NaturalPerson',
        'basic': '#/components/schemas/BasicPerson'
    }
    assert components['MetaPersonRequest']['oneOf'] == [
        {'$ref': '#/components/schemas/NaturalPersonRequest'},
    ]
    assert components['MetaPersonRequest']['discriminator']['mapping'] == {
        'natural': '#/components/schemas/NaturalPersonRequest',
    }


def test_polymorphic_forced_many_false(no_warnings):
    class XViewSet(viewsets.GenericViewSet):
        @extend_schema(
            responses=PolymorphicProxySerializer(
                component_name='MetaPerson',
                serializers=[NaturalPersonSerializer, LegalPersonSerializer],
                resource_type_field_name='type',
                many=False
            )
        )
        def list(self, request, *args, **kwargs):
            return Response({})  # pragma: no cover

    schema = generate_schema('x', XViewSet)
    assert get_response_schema(schema['paths']['/x/']['get']) == {
        '$ref': '#/components/schemas/MetaPerson'
    }


def test_polymorphic_manual_many(no_warnings):
    mixed_poly = PolymorphicProxySerializer(
        component_name='MetaLegalPerson',
        serializers=[NaturalPersonSerializer, NaturalPersonSerializer(many=True)],
        resource_type_field_name=None,
        many=False,
    )

    class XViewSet(viewsets.GenericViewSet):
        @extend_schema(request=mixed_poly, responses=mixed_poly)
        def create(self, request, *args, **kwargs):
            return Response({})  # pragma: no cover

        @extend_schema(responses=mixed_poly)
        def list(self, request, *args, **kwargs):
            return Response({})  # pragma: no cover

    schema = generate_schema('x', XViewSet)
    response_schema = get_response_schema(schema['paths']['/x/']['post'])
    request_schema = get_request_schema(schema['paths']['/x/']['post'])
    assert response_schema == request_schema == {'$ref': '#/components/schemas/MetaLegalPerson'}
    assert schema['components']['schemas']['MetaLegalPerson'] == {
        'oneOf': [
            {'$ref': '#/components/schemas/NaturalPerson'},
            {'type': 'array', 'items': {'$ref': '#/components/schemas/NaturalPerson'}}
        ]
    }
