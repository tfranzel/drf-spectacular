from rest_framework import serializers, viewsets
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
                'Create Error 403 Example',
                value={'field': 'error'},
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
