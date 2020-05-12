from rest_framework import fields, serializers, viewsets, mixins
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.extensions import OpenApiSerializerFieldExtension, OpenApiViewExtension
from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from drf_spectacular.validation import validate_schema
from tests import generate_schema, get_response_schema


class Base64Field(fields.Field):
    pass  # pragma: no cover


def test_serializer_field_extension(no_warnings):
    class Base64FieldExtension(OpenApiSerializerFieldExtension):
        target_class = 'tests.test_extensions.Base64Field'

        def map_serializer_field(self, auto_schema):
            return build_basic_type(OpenApiTypes.BYTE)

    class XSerializer(serializers.Serializer):
        hash = Base64Field()

    class XViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
        serializer_class = XSerializer

    schema = generate_schema('x', XViewset)
    validate_schema(schema)
    assert schema['components']['schemas']['X']['properties']['hash']['type'] == 'string'
    assert schema['components']['schemas']['X']['properties']['hash']['format'] == 'byte'


class XView(APIView):
    """ underspecified library view """
    def get(self):
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
    validate_schema(schema)
    operation = schema['paths']['/x']['get']
    assert get_response_schema(operation)['type'] == 'number'


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
    validate_schema(schema)
    operation = schema['paths']['/x']['get']
    assert get_response_schema(operation)['type'] == 'number'
