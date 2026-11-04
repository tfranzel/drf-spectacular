import typing
from unittest import mock

from rest_framework import pagination, serializers, viewsets
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema
from tests import generate_schema, get_request_schema, get_response_schema
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


@mock.patch('drf_spectacular.settings.spectacular_settings.OAS_VERSION', '3.1.0')
def test_oas31_pagination_and_type_hint_nullable(no_warnings):
    class SubTypedDict(typing.TypedDict):
        label: typing.Optional[str]
        items: typing.List[typing.Optional[int]]

    class XSerializer(serializers.Serializer):
        td = serializers.SerializerMethodField()
        nullable_td = serializers.SerializerMethodField(allow_null=True)
        nullable_union = serializers.SerializerMethodField(allow_null=True)

        def get_td(self, obj) -> SubTypedDict:
            pass  # pragma: no cover

        def get_nullable_td(self, obj) -> typing.Optional[SubTypedDict]:
            pass  # pragma: no cover

        def get_nullable_union(self, obj) -> typing.Union[int, str, None]:
            pass  # pragma: no cover

    class XViewset(viewsets.ModelViewSet):
        serializer_class = XSerializer
        queryset = SimpleModel.objects.none()
        pagination_class = pagination.PageNumberPagination

        @extend_schema(request=typing.Optional[int], responses=typing.Optional[int])
        def create(self, request, *args, **kwargs):
            pass  # pragma: no cover

    schema = generate_schema('x', XViewset)
    schemas = schema['components']['schemas']

    assert schemas['X']['properties'] == {
        'td': {
            'type': 'object',
            'properties': {
                'label': {'type': ['string', 'null']},
                'items': {'type': 'array', 'items': {'type': ['integer', 'null']}},
            },
            'required': ['items', 'label'],
            'readOnly': True,
        },
        'nullable_td': {
            'type': ['object', 'null'],
            'properties': {
                'label': {'type': ['string', 'null']},
                'items': {'type': 'array', 'items': {'type': ['integer', 'null']}},
            },
            'required': ['items', 'label'],
            'readOnly': True,
        },
        'nullable_union': {
            'oneOf': [{'type': 'integer'}, {'type': 'string'}, {'type': 'null'}],
            'readOnly': True,
        },
    }
    assert schemas['PaginatedXList'] == {
        'type': 'object',
        'required': ['count', 'results'],
        'properties': {
            'count': {'type': 'integer', 'example': 123},
            'next': {
                'type': ['string', 'null'],
                'format': 'uri',
                'example': 'http://api.example.org/accounts/?page=4',
            },
            'previous': {
                'type': ['string', 'null'],
                'format': 'uri',
                'example': 'http://api.example.org/accounts/?page=2',
            },
            'results': {'type': 'array', 'items': {'$ref': '#/components/schemas/X'}},
        },
    }
    post_op = schema['paths']['/x/']['post']
    assert get_request_schema(post_op) == {'type': ['integer', 'null']}
    assert get_response_schema(post_op) == {'type': ['integer', 'null']}
