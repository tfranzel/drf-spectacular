import pytest
from rest_framework import __version__ as DRF_VERSION  # type: ignore[attr-defined]
from rest_framework import generics, pagination, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample, OpenApiParameter, extend_schema, extend_schema_serializer,
)
from tests import assert_schema, generate_schema
from tests.models import SimpleModel


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
