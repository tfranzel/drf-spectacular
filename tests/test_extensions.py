from rest_framework import fields, serializers, viewsets, mixins

from drf_spectacular.fields import OpenApiSerializerFieldExtension
from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.validation import validate_schema
from tests import generate_schema


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
    schema['components']['schemas']['X']['properties']['hash']['type'] == 'string'
    schema['components']['schemas']['X']['properties']['hash']['format'] == 'byte'
