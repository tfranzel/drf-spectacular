from unittest import mock

from rest_framework import serializers, viewsets, routers
from rest_framework.response import Response

from drf_spectacular.openapi import SchemaGenerator, AutoSchema
from drf_spectacular.renderers import NoAliasOpenAPIRenderer
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, QueryParameter


class AlphaSerializer(serializers.Serializer):
    field_a = serializers.CharField()
    field_b = serializers.IntegerField()


class BetaSerializer(AlphaSerializer):
    field_c = serializers.JSONField()


class ErrorSerializer(serializers.Serializer):
    msg = serializers.CharField()
    code = serializers.IntegerField()


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
                QueryParameter(name='expiration_date', type=OpenApiTypes.DATETIME, description='time the object will expire at'),
                QueryParameter(name='test_mode', type=bool, description='creation will be in the sandbox'),
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
    schema_yml = NoAliasOpenAPIRenderer().render(schema, renderer_context={})

    with open('tests/test_extend_schema.yml') as fh:
        assert schema_yml.decode() == fh.read()
