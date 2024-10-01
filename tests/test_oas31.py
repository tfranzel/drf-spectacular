from unittest import mock

from rest_framework import serializers, viewsets
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema
from tests import generate_schema
from tests.models import SimpleModel


@mock.patch('drf_spectacular.settings.spectacular_settings.OAS_VERSION', '3.1.0')
def test_nullable_sub_serializer(no_warnings):
    class XSerializer(serializers.Serializer):
        f = serializers.FloatField(allow_null=True)

    class YSerializer(serializers.Serializer):
        x = XSerializer(allow_null=True)

    class XAPIView(APIView):
        @extend_schema(responses=YSerializer)
        def get(self, request):
            pass  # pragma: no cover

    schema = generate_schema('x', view=XAPIView)

    assert schema['components']['schemas'] == {
        'X': {
            'properties': {'f': {'format': 'double', 'type': ['number', 'null']}},
            'required': ['f'],
            'type': 'object'
        },
        'Y': {
            'properties': {'x': {'oneOf': [{'$ref': '#/components/schemas/X'}, {'type': 'null'}]}},
            'required': ['x'],
            'type': 'object'
        }
    }


@mock.patch('drf_spectacular.settings.spectacular_settings.OAS_VERSION', '3.1.0')
def test_nullable_enum_resolution(no_warnings):
    class XSerializer(serializers.Serializer):
        foo = serializers.ChoiceField(
            choices=[('A', 'A'), ('B', 'B')],
            allow_null=True
        )

    class XAPIView(APIView):
        @extend_schema(responses=XSerializer)
        def get(self, request):
            pass  # pragma: no cover

    schema = generate_schema('x', view=XAPIView)

    assert schema['components']['schemas']['FooEnum'] == {
        'description': '* `A` - A\n* `B` - B',
        'enum': ['A', 'B'],
        'type': 'string',
    }
    assert schema['components']['schemas']['X'] == {
        'properties': {
            'foo': {
                'oneOf': [
                    {'$ref': '#/components/schemas/FooEnum'},
                    {'$ref': '#/components/schemas/NullEnum'}
                ]
            }
        },
        'required': ['foo'],
        'type': 'object'
    }


@mock.patch('drf_spectacular.settings.spectacular_settings.OAS_VERSION', '3.1.0')
def test_validator_addition_for_oas31(no_warnings):

    class XSerializer(serializers.Serializer):
        field = serializers.CharField(allow_blank=True, allow_null=True, max_length=40, required=False)

    class XViewset(viewsets.ModelViewSet):
        serializer_class = XSerializer
        queryset = SimpleModel.objects.none()

    schema = generate_schema('x', XViewset)

    assert schema['components']['schemas']['X'] == {
        'properties': {
            'field': {'maxLength': 40, 'type': ['string', 'null']}
        },
        'type': 'object'
    }
