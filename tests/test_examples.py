from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from drf_spectacular.utils import (
    OpenApiExample, OpenApiParameter, extend_schema, extend_schema_serializer,
)
from tests import assert_schema, generate_schema, get_request_schema, get_response_schema


@extend_schema_serializer(examples=[
    OpenApiExample(
        'ex1',
        summary='i_am_summary',
        value={"field": "aaa11"},
        response_only=True,
    ),
    OpenApiExample(
        'ex2',
        summary='i_am_summary2',
        value={"field": "aaa22"},
        request_only=True,
    ),
    OpenApiExample(
        'ex3',
        summary='i_am_summary3',
        value={'field': 'aaa33'}
    )
])
class ASerializer(serializers.Serializer):
    field = serializers.IntegerField()


class BSerializer(serializers.Serializer):
    field = serializers.IntegerField()


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'ex_c',
            summary='i_am_summary',
            value={"field": 232323},
            response_only=True,
        ),
        OpenApiExample(
            'ex_c2',
            summary='i_am_summary',
            value={"field": 232323},
            request_only=True,
        ),
    ]
)
class CSerializer(serializers.Serializer):
    field = serializers.IntegerField()


@extend_schema(responses=BSerializer)
class ExampleTestWithExtendedViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = ASerializer

    @extend_schema(
        request=ASerializer,
        responses={'200': BSerializer},
        examples=[
            OpenApiExample(
                'example1',
                summary='i_am_ex1', response_only=True,
                value={'field': 11}),
            OpenApiExample(
                'example2',
                summary='i_am_ex2', request_only=True,
                value={'field': 12}),
            OpenApiExample(
                'example3',
                summary='i_am_ex3',
                value={'field': 13}),
            OpenApiExample(
                'example4',
                summary='i_am_ex3',
                value={'field': 14},
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
                        "ex1",
                        summary="i_am_query_param_ex",
                        value="aaa",
                        description="i am description"
                    ),
                    OpenApiExample(
                        "ex2",
                        summary="i_am_query_param_ex2",
                        value="bbbb",
                        description="qqqqqqq"
                    )
                ]
            ),
        ],
        responses={'200': CSerializer},
    )
    def list(self, request):
        return Response()  # pragma: no cover

    @action(detail=False, methods=['GET'])
    def raw_action(self, request):
        return Response()  # pragma: no cover

    @extend_schema(request=ASerializer, responses={'200': BSerializer})
    @action(detail=False, methods=['POST'])
    def override_extend_schema_action(self, request):
        return Response()  # pragma: no cover


def test_examples(no_warnings):
    assert_schema(
        generate_schema('schema', ExampleTestWithExtendedViewSet),
        'tests/test_examples.yml',
    )


def test_extend_schema_serializer_with_examples(no_warnings):
    schema = generate_schema('x', ExampleTestWithExtendedViewSet)
    create_body_op = get_request_schema(schema['paths']['/x/']['post'])
    create_op = get_response_schema(schema['paths']['/x/']['post'])
    list_op = get_response_schema(schema['paths']['/x/']['get'])
    override_extend_schema_action_op = get_response_schema(
        schema['paths']['/x/override_extend_schema_action/']['post']
    )
    create_request_examples = schema['paths']['/x/']['post']['requestBody']['content']['application/json'][
        'examples']
    list_response_examples = schema['paths']['/x/']['get']['responses']['200']['content']['application/json'][
        'examples']

    assert create_body_op['$ref'].endswith('A')
    assert create_op['$ref'].endswith('B')
    assert list_op['items']['$ref'].endswith('C')
    assert override_extend_schema_action_op['$ref'].endswith('B')
    assert create_request_examples.get('example2')
    assert create_request_examples['example2']['value'] == {'field': 12}
    assert create_request_examples.get('example3')
    assert create_request_examples['example3']['value'] == {'field': 13}
    assert list_response_examples.get('ex_c')
    assert list_response_examples['ex_c']['summary'] == 'i_am_summary'
    assert list_response_examples.get('ex_c2') is None


def test_extend_schema_on_view_and_method_with_examples(no_warnings):
    schema = generate_schema('x', ExampleTestWithExtendedViewSet)
    create_body_op = get_request_schema(schema['paths']['/x/']['post'])
    create_op = get_response_schema(schema['paths']['/x/']['post'])
    list_op = get_response_schema(schema['paths']['/x/']['get'])
    raw_action_op = get_response_schema(schema['paths']['/x/raw_action/']['get'])
    parameter_examples = schema['paths']['/x/']['get']['parameters'][0]['examples']

    assert create_body_op['$ref'].endswith('A')
    assert create_op['$ref'].endswith('B')
    assert list_op['items']['$ref'].endswith('C')
    assert raw_action_op['$ref'].endswith('B')
    assert parameter_examples.get('ex1') is not None
    assert parameter_examples['ex1']['value'] == 'aaa'
    assert parameter_examples.get('ex2') is not None
    assert parameter_examples['ex2']['value'] == 'bbbb'
