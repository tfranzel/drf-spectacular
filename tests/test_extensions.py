from rest_framework import fields, mixins, permissions, serializers, viewsets
from rest_framework.authentication import BaseAuthentication
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.extensions import (
    OpenApiAuthenticationExtension, OpenApiSerializerFieldExtension, OpenApiViewExtension,
)
from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from tests import generate_schema, get_response_schema
from tests.models import SimpleModel, SimpleSerializer


class Base64Field(fields.Field):
    pass  # pragma: no cover


def test_serializer_field_extension(no_warnings):
    class Base64FieldExtension(OpenApiSerializerFieldExtension):
        target_class = 'tests.test_extensions.Base64Field'

        def map_serializer_field(self, auto_schema, direction):
            return build_basic_type(OpenApiTypes.BYTE)

    class XSerializer(serializers.Serializer):
        hash = Base64Field()

    class XViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
        serializer_class = XSerializer

    schema = generate_schema('x', XViewset)
    assert schema['components']['schemas']['X']['properties']['hash']['type'] == 'string'
    assert schema['components']['schemas']['X']['properties']['hash']['format'] == 'byte'


class Base32Field(fields.Field):
    pass  # pragma: no cover


def test_serializer_field_extension_with_breakout(no_warnings):
    class Base32FieldExtension(OpenApiSerializerFieldExtension):
        target_class = 'tests.test_extensions.Base32Field'

        def get_name(self):
            return 'FieldComponentName'

        def map_serializer_field(self, auto_schema, direction):
            return build_basic_type(OpenApiTypes.BYTE)

    class XSerializer(serializers.Serializer):
        hash = Base32Field()

    class XViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
        serializer_class = XSerializer

    schema = generate_schema('x', XViewset)
    assert schema['components']['schemas']['FieldComponentName'] == {
        'type': 'string', 'format': 'byte'
    }


class XView(APIView):
    """ underspecified library view """
    def get(self):
        """ docstring for GET """
        return Response(1.234)  # pragma: no cover


def test_view_extension(no_warnings):
    class FixXView(OpenApiViewExtension):
        target_class = 'tests.test_extensions.XView'

        def view_replacement(self):
            class Fixed(self.target_class):
                @extend_schema(responses=OpenApiTypes.FLOAT)
                def get(self, request):
                    pass  # pragma: no cover

            return Fixed

    schema = generate_schema('x', view=XView)
    operation = schema['paths']['/x']['get']
    assert get_response_schema(operation)['type'] == 'number'
    assert operation['description'] == 'docstring for GET'


@api_view()
def x_view_function():
    """ underspecified library view """
    return Response(1.234)  # pragma: no cover


def test_view_function_extension(no_warnings):
    class FixXFunctionView(OpenApiViewExtension):
        target_class = 'tests.test_extensions.x_view_function'

        def view_replacement(self):
            fixed = extend_schema(responses=OpenApiTypes.FLOAT)(self.target_class)
            return fixed

    schema = generate_schema('x', view_function=x_view_function)
    operation = schema['paths']['/x']['get']
    assert get_response_schema(operation)['type'] == 'number'
    assert operation['description'].strip() == 'underspecified library view'


def test_extension_not_found_for_installed_app(capsys):
    class FixXFunctionView(OpenApiViewExtension):
        target_class = 'tests.test_extensions.NotExistingClass'

        def view_replacement(self):
            pass  # pragma: no cover

    OpenApiViewExtension.get_match(object())
    assert 'target class was not found' in capsys.readouterr().err


class MultiHeaderAuth(BaseAuthentication):
    pass


def test_multi_auth_scheme_extension(no_warnings):
    class MultiHeaderAuthExtension(OpenApiAuthenticationExtension):
        target_class = 'tests.test_extensions.MultiHeaderAuth'
        name = ['apiKey', 'appId']

        def get_security_definition(self, auto_schema):
            return [
                {'type': 'apiKey', 'in': 'header', 'name': 'X-API-KEY'},
                {'type': 'apiKey', 'in': 'header', 'name': 'X-APP-ID'},
            ]

    class XViewset(viewsets.ReadOnlyModelViewSet):
        queryset = SimpleModel.objects.none()
        serializer_class = SimpleSerializer
        authentication_classes = [MultiHeaderAuth]
        permission_classes = [permissions.IsAuthenticated]

    schema = generate_schema('/x', XViewset)
    assert schema['components']['securitySchemes'] == {
        'apiKey': {'type': 'apiKey', 'in': 'header', 'name': 'X-API-KEY'},
        'appId': {'type': 'apiKey', 'in': 'header', 'name': 'X-APP-ID'}
    }
    assert schema['paths']['/x/']['get']['security'] == [{'apiKey': [], 'appId': []}]
