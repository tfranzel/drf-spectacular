from unittest import mock

from rest_framework import serializers, viewsets, routers
from rest_framework.response import Response

from drf_spectacular.openapi import SchemaGenerator, AutoSchema
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, ExtraParameter, extend_schema_field
from tests import assert_schema


class AlphaSerializer(serializers.Serializer):
    field_a = serializers.CharField()
    field_b = serializers.IntegerField()


class BetaSerializer(AlphaSerializer):
    field_c = serializers.JSONField()


class InlineSerializer(serializers.Serializer):
    inline_b = serializers.BooleanField()
    inline_i = serializers.IntegerField()


class ErrorSerializer(serializers.Serializer):
    field_i = serializers.SerializerMethodField()
    field_j = serializers.SerializerMethodField()
    field_k = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.DATETIME)
    def get_field_i(self, object):
        return '2020-03-06 20:54:00.104248'

    @extend_schema_field(InlineSerializer)
    def get_field_j(self, object):
        return InlineSerializer({}).data

    @extend_schema_field(InlineSerializer(many=True))
    def get_field_k(self, object):
        return InlineSerializer([], many=True).data


with mock.patch('rest_framework.settings.api_settings.DEFAULT_SCHEMA_CLASS', AutoSchema):
    class FirstViewset(viewsets.GenericViewSet):
        serializer_class = AlphaSerializer

        @extend_schema(
            operation_id='customname_create',
            request=AlphaSerializer,
            responses={
                201: BetaSerializer(many=True),
                500: ErrorSerializer,
            },
            extra_parameters=[
                ExtraParameter('expiration_date', OpenApiTypes.DATETIME, description='time the object will expire at'),
                ExtraParameter('test_mode', bool, location=ExtraParameter.HEADER, description='creation will be in the sandbox'),
            ],
            description='this weird endpoint needs some explaining',
        )
        def create(self, request, *args, **kwargs):
            return Response({})


@mock.patch('rest_framework.settings.api_settings.DEFAULT_SCHEMA_CLASS', AutoSchema)
def test_extend_schema():
    router = routers.SimpleRouter()
    router.register('doesitall', FirstViewset, basename="doesitall")
    generator = SchemaGenerator(patterns=router.urls)
    schema = generator.get_schema(request=None, public=True)

    assert_schema(schema, 'tests/test_extend_schema.yml')
