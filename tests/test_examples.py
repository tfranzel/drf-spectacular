import pytest
from rest_framework import __version__ as DRF_VERSION  # type: ignore[attr-defined]
from rest_framework import generics, pagination, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_serializer,
)
from tests import assert_schema, generate_schema
from tests.models import SimpleModel, SimpleSerializer


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Serializer A Example RO',
            value={"field": 1},
            response_only=True,
        ),
        OpenApiExample(
            'Serializer A Example WO',
            value={"field": 2},
            request_only=True,
        ),
        OpenApiExample(
            'Serializer A Example RW',
            summary='Serializer A Example RW custom summary',
            value={'field': 3}
        ),
        OpenApiExample(
            'Serializer A Example RW External',
            external_value='https://example.com/example_a.txt',
            media_type='application/x-www-form-urlencoded'
        )
    ]
)
class ASerializer(serializers.Serializer):
    field = serializers.IntegerField()


class BSerializer(serializers.Serializer):
    field = serializers.IntegerField()


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Serializer C Example RO',
            value={"field": 111},
            response_only=True,
        ),
        OpenApiExample(
            'Serializer C Example WO',
            value={"field": 222},
            request_only=True,
        ),
    ]
)
class CSerializer(serializers.Serializer):
    field = serializers.IntegerField()


@extend_schema(
    responses=BSerializer,
    examples=[OpenApiExample("Example ID 1", value=1, parameter_only=('id', 'path'))]
)
class ExampleTestWithExtendedViewSet(viewsets.GenericViewSet):
    serializer_class = ASerializer
    queryset = SimpleModel.objects.none()

    @extend_schema(
        request=ASerializer,
        responses={
            201: BSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Create Example RO',
                value={'field': 11},
                response_only=True,
            ),
            OpenApiExample(
                'Create Example WO',
                value={'field': 22},
                request_only=True,
            ),
            OpenApiExample(
                'Create Example RW',
                value={'field': 33},
            ),
            OpenApiExample(
                'Create Error 403 Integer Example',
                value={'field': 'error (int)'},
                response_only=True,
                status_codes=[status.HTTP_403_FORBIDDEN],
            ),
            OpenApiExample(
                'Create Error 403 String Example',
                value={'field': 'error (str)'},
                response_only=True,
                status_codes=['403']
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)  # pragma: no cover

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="artist",
                description="Filter by artist",
                required=False,
                type=str,
                examples=[
                    OpenApiExample(
                        "Artist Query Example 1",
                        value="prince",
                        description="description for artist query example 1"
                    ),
                    OpenApiExample(
                        "Artist Query Example 2",
                        value="miles davis",
                        description="description for artist query example 2"
                    )
                ]
            ),
        ],
        responses=CSerializer,
    )
    def list(self, request):
        return Response()  # pragma: no cover

    @extend_schema(
        examples=[
            OpenApiExample(
                "Example ID 2",
                value=2,
                parameter_only=('id', OpenApiParameter.PATH)
            )
        ]
    )
    def retrieve(self, request):
        return Response()  # pragma: no cover

    @action(detail=False, methods=['GET'])
    def raw_action(self, request):
        return Response()  # pragma: no cover

    @extend_schema(responses=BSerializer)
    @action(detail=False, methods=['POST'])
    def override_extend_schema_action(self, request):
        return Response()  # pragma: no cover


def test_examples(no_warnings):
    assert_schema(
        generate_schema('schema', ExampleTestWithExtendedViewSet),
        'tests/test_examples.yml',
    )


@pytest.mark.skipif(DRF_VERSION < '3.12', reason='DRF pagination schema broken')
def test_example_pagination(no_warnings):
    class PaginatedExamplesViewSet(ExampleTestWithExtendedViewSet):
        pagination_class = pagination.LimitOffsetPagination

    schema = generate_schema('e', PaginatedExamplesViewSet)
    operation = schema['paths']['/e/']['get']
    assert operation['responses']['200']['content']['application/json']['examples'] == {
        'SerializerCExampleRO': {
            'value': {
                'count': 123,
                'next': 'http://api.example.org/accounts/?offset=400&limit=100',
                'previous': 'http://api.example.org/accounts/?offset=200&limit=100',
                'results': [{'field': 111}],
            },
            'summary': 'Serializer C Example RO'
        }
    }


@pytest.mark.skipif(DRF_VERSION < '3.12', reason='DRF pagination schema broken')
def test_example_nested_pagination(no_warnings):
    class NestedPagination(pagination.LimitOffsetPagination):
        def get_paginated_response_schema(self, schema):
            return {
                'type': 'object',
                'required': ['pagination', 'results'],
                'properties': {
                    'pagination': {
                        'type': 'object',
                        'required': ['next', 'previous'],
                        'properties': {
                            'count': {
                                'type': 'integer',
                                'example': 123,
                            },
                            'next': {
                                'type': 'string',
                                'nullable': True,
                                'format': 'uri',
                                'example': 'http://api.example.org/accounts/?{offset_prm}=400&{limit_prm}=100'.format(
                                    offset_prm=self.offset_query_param, limit_prm=self.limit_query_param),
                            },
                            'previous': {
                                'type': 'string',
                                'nullable': True,
                                'format': 'uri',
                                'example': 'http://api.example.org/accounts/?{offset_prm}=200&{limit_prm}=100'.format(
                                    offset_prm=self.offset_query_param, limit_prm=self.limit_query_param),
                            },
                        }
                    },
                    'results': schema,
                },
            }

    class PaginatedExamplesViewSet(ExampleTestWithExtendedViewSet):
        pagination_class = NestedPagination

    schema = generate_schema('e', PaginatedExamplesViewSet)
    operation = schema['paths']['/e/']['get']
    assert operation['responses']['200']['content']['application/json']['examples'] == {
        'SerializerCExampleRO': {
            'value': {
                'pagination': {
                    'count': 123,
                    'next': 'http://api.example.org/accounts/?offset=400&limit=100',
                    'previous': 'http://api.example.org/accounts/?offset=200&limit=100',
                },
                'results': [{'field': 111}],
            },
            'summary': 'Serializer C Example RO'
        }
    }


def test_example_request_response_listed_examples(no_warnings):
    @extend_schema(
        request=ASerializer(many=True),
        responses=ASerializer(many=True),
        examples=[
            OpenApiExample('Ex', {'id': '1234'})
        ]
    )
    class XView(generics.CreateAPIView):
        pass

    schema = generate_schema('e', view=XView)
    operation = schema['paths']['/e']['post']
    assert operation['requestBody']['content']['application/json'] == {
        'schema': {'type': 'array', 'items': {'$ref': '#/components/schemas/A'}},
        'examples': {'Ex': {'value': [{'id': '1234'}]}}
    }
    assert operation['responses']['201']['content']['application/json'] == {
        'schema': {'type': 'array', 'items': {'$ref': '#/components/schemas/A'}},
        'examples': {'Ex': {'value': [{'id': '1234'}]}}
    }


def test_examples_list_detection_on_non_200_decoration(no_warnings):
    class ExceptionSerializer(serializers.Serializer):
        api_status_code = serializers.CharField()
        extra = serializers.DictField(required=False)

    @extend_schema(
        responses={
            200: SimpleSerializer,
            400: OpenApiResponse(
                response=ExceptionSerializer,
                examples=[
                    OpenApiExample(
                        "Date parse error",
                        value={"api_status_code": "DATE_PARSE_ERROR", "extra": {"details": "foobar"}},
                        status_codes=['400']
                    )
                ],
            ),
        },
    )
    class XListView(generics.ListAPIView):
        model = SimpleModel
        serializer_class = SimpleSerializer
        pagination_class = pagination.LimitOffsetPagination

    schema = generate_schema('/x/', view=XListView)
    # regular response listed/paginated
    assert schema['paths']['/x/']['get']['responses']['200']['content']['application/json'] == {
        'schema': {'$ref': '#/components/schemas/PaginatedSimpleList'}
    }
    # non-200 error response example NOT listed/paginated
    assert schema['paths']['/x/']['get']['responses']['400']['content']['application/json'] == {
        'examples': {
            'DateParseError': {
                'summary': 'Date parse error',
                'value': {'api_status_code': 'DATE_PARSE_ERROR', 'extra': {'details': 'foobar'}}
            }
        },
        'schema': {'$ref': '#/components/schemas/Exception'},
    }


def test_inherited_status_code_from_response_container(no_warnings):
    @extend_schema(
        responses={
            400: OpenApiResponse(
                response=SimpleSerializer,
                examples=[
                    # prior to the fix this required the argument status_code=[400]
                    # as the code was not passed down and the filtering sorted it out.
                    OpenApiExample("an example", value={"id": 3})
                ],
            ),
        },
    )
    class XListView(generics.ListAPIView):
        model = SimpleModel
        serializer_class = SimpleSerializer

    schema = generate_schema('/x/', view=XListView)
    assert schema['paths']['/x/']['get']['responses']['400']['content']['application/json'] == {
        'schema': {'$ref': '#/components/schemas/Simple'},
        'examples': {'AnExample': {'value': {'id': 3}, 'summary': 'an example'}}
    }


def test_examples_with_falsy_values(no_warnings):
    @extend_schema(
        responses=OpenApiResponse(
            description='something',
            response=OpenApiTypes.JSON_PTR,
            examples=[
                OpenApiExample('one', value=1),
                OpenApiExample('empty-list', value=[]),
                OpenApiExample('false', value=False),
                OpenApiExample('zero', value=0),
                OpenApiExample('empty'),
            ],
        ),
    )
    class XListView(generics.ListAPIView):
        model = SimpleModel
        serializer_class = SimpleSerializer

    schema = generate_schema('/x/', view=XListView)
    assert schema['paths']['/x/']['get']['responses']['200']['content']['application/json']['examples'] == {
        'One': {'summary': 'one', 'value': 1},
        'Empty-list': {'summary': 'empty-list', 'value': []},
        'False': {'summary': 'false', 'value': False},
        'Zero': {'summary': 'zero', 'value': 0},
        'Empty': {'summary': 'empty'},
    }


@pytest.mark.skipif(DRF_VERSION < '3.12', reason='DRF pagination schema broken')
def test_plain_pagination_example(no_warnings):

    class PlainPagination(pagination.LimitOffsetPagination):
        """ return a (unpaginated) basic list, while other might happen in the headers """

        def get_paginated_response_schema(self, schema):
            return schema

    class PaginatedExamplesViewSet(ExampleTestWithExtendedViewSet):
        pagination_class = PlainPagination

    schema = generate_schema('e', PaginatedExamplesViewSet)
    operation = schema['paths']['/e/']['get']
    assert operation['responses']['200']['content']['application/json']['examples'] == {
        'SerializerCExampleRO': {
            'value': [{'field': 111}],
            'summary': 'Serializer C Example RO'
        }
    }
