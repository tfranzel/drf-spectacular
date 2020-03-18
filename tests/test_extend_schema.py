from unittest import mock

from django.utils.http import urlsafe_base64_encode
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, extend_schema_field
from tests import assert_schema, generate_schema


class AlphaSerializer(serializers.Serializer):
    field_a = serializers.CharField()
    field_b = serializers.IntegerField()


class BetaSerializer(AlphaSerializer):
    field_c = serializers.JSONField()


@extend_schema_field(OpenApiTypes.BYTE)
class CustomField(serializers.Field):
    def to_representation(self, value):
        return urlsafe_base64_encode(b'\xf0\xf1\xf2')


class GammaSerializer(serializers.Serializer):
    encoding = serializers.CharField()
    image_data = CustomField()


class InlineSerializer(serializers.Serializer):
    inline_b = serializers.BooleanField()
    inline_i = serializers.IntegerField()


class ErrorDetailSerializer(serializers.Serializer):
    field_i = serializers.SerializerMethodField()
    field_j = serializers.SerializerMethodField()
    field_k = serializers.SerializerMethodField()
    field_l = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.DATETIME)
    def get_field_i(self, object):
        return '2020-03-06 20:54:00.104248'

    @extend_schema_field(InlineSerializer)
    def get_field_j(self, object):
        return InlineSerializer({}).data

    @extend_schema_field(InlineSerializer(many=True))
    def get_field_k(self, object):
        return InlineSerializer([], many=True).data

    @extend_schema_field(serializers.ChoiceField(choices=['a', 'b']))
    def get_field_l(self, object):
        return object.some_choice


with mock.patch('rest_framework.settings.api_settings.DEFAULT_SCHEMA_CLASS', AutoSchema):
    class DoesItAllViewset(viewsets.GenericViewSet):
        serializer_class = AlphaSerializer

        @extend_schema(
            operation_id='customname_create',
            request=AlphaSerializer,
            responses={
                201: BetaSerializer(many=True),
                200: GammaSerializer,
                500: ErrorDetailSerializer,
            },
            parameters=[
                OpenApiParameter('expiration_date', OpenApiTypes.DATETIME, description='time the object will expire at'),
                OpenApiParameter('test_mode', bool, location=OpenApiParameter.HEADER, description='creation will be in the sandbox', enum=[True, False]),
            ],
            description='this weird endpoint needs some explaining',
            deprecated=True,
            tags=['custom_tag'],
        )
        def create(self, request, *args, **kwargs):
            return Response({})

        @extend_schema(exclude=True)
        def list(self, request, *args, **kwargs):
            return Response([])

        @extend_schema(
            parameters=[OpenApiParameter('id', OpenApiTypes.UUID, OpenApiParameter.PATH)],
            request=OpenApiTypes.NONE,
            responses={201: None},
        )
        @action(detail=True, methods=['POST'])
        def subscribe(self, request):
            return Response(status=201)

        @extend_schema(request=OpenApiTypes.OBJECT, responses={201: None})
        @action(detail=False, methods=['POST'])
        def callback(self, request):
            return Response(status=201)


@mock.patch('rest_framework.settings.api_settings.DEFAULT_SCHEMA_CLASS', AutoSchema)
def test_extend_schema(no_warnings):
    assert_schema(
        generate_schema('doesitall', DoesItAllViewset),
        'tests/test_extend_schema.yml'
    )
