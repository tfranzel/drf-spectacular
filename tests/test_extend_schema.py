from unittest import mock

from django.utils.http import urlsafe_base64_encode
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_field
from tests import assert_schema, generate_schema, get_response_schema


class AlphaSerializer(serializers.Serializer):
    field_a = serializers.CharField()
    field_b = serializers.IntegerField()


class BetaSerializer(AlphaSerializer):
    field_c = serializers.JSONField()


class DeltaSerializer(serializers.Serializer):
    field_a = serializers.CharField(required=False)
    field_b = serializers.IntegerField(required=False)


@extend_schema_field(OpenApiTypes.BYTE)
class CustomField(serializers.Field):
    def to_representation(self, value):
        return urlsafe_base64_encode(b'\xf0\xf1\xf2')  # pragma: no cover


class GammaSerializer(serializers.Serializer):
    encoding = serializers.CharField()
    image_data = CustomField()


class InlineSerializer(serializers.Serializer):
    inline_b = serializers.BooleanField()
    inline_i = serializers.IntegerField()


class QuerySerializer(serializers.Serializer):
    stars = serializers.IntegerField(min_value=1, max_value=5, help_text='filter by rating stars')
    contains = serializers.CharField(
        min_length=3, max_length=10, help_text='filter by containing string', required=False
    )
    order_by = serializers.MultipleChoiceField(
        choices=['a', 'b'],
        default=['a'],
    )


class ErrorDetailSerializer(serializers.Serializer):
    field_i = serializers.SerializerMethodField()
    field_j = serializers.SerializerMethodField()
    field_k = serializers.SerializerMethodField()
    field_l = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.DATETIME)
    def get_field_i(self, object):
        return '2020-03-06 20:54:00.104248'  # pragma: no cover

    @extend_schema_field(InlineSerializer(allow_null=True))
    def get_field_j(self, object):
        return InlineSerializer({}).data  # pragma: no cover

    @extend_schema_field(InlineSerializer(many=True))
    def get_field_k(self, object):
        return InlineSerializer([], many=True).data  # pragma: no cover

    @extend_schema_field(serializers.ChoiceField(choices=['a', 'b']))
    def get_field_l(self, object):
        return object.some_choice  # pragma: no cover


with mock.patch('rest_framework.settings.api_settings.DEFAULT_SCHEMA_CLASS', AutoSchema):
    class DoesItAllViewset(viewsets.GenericViewSet):
        serializer_class = AlphaSerializer

        @extend_schema(
            operation_id='customname_create',
            request=AlphaSerializer,
            responses={
                200: BetaSerializer(many=True),
                201: GammaSerializer,
                500: ErrorDetailSerializer,
            },
            parameters=[
                OpenApiParameter(
                    'expiration_date', OpenApiTypes.DATETIME, description='time the object will expire at'
                ),
                OpenApiParameter(
                    'test_mode', bool, location=OpenApiParameter.HEADER, enum=[True, False],
                    description='creation will be in the sandbox',
                )
            ],
            description='this weird endpoint needs some explaining',
            summary='short summary',
            deprecated=True,
            tags=['custom_tag'],
        )
        def create(self, request, *args, **kwargs):
            return Response({})  # pragma: no cover

        @extend_schema(exclude=True)
        def list(self, request, *args, **kwargs):
            return Response([])  # pragma: no cover

        @extend_schema(
            parameters=[OpenApiParameter('id', OpenApiTypes.INT, OpenApiParameter.PATH)],
            request=None,
            responses={201: None},
        )
        @action(detail=True, methods=['POST'])
        def subscribe(self, request):
            return Response(status=201)  # pragma: no cover

        @extend_schema(
            request=OpenApiTypes.OBJECT,
            responses={201: None},
            parameters=[OpenApiParameter('ephemeral', OpenApiTypes.UUID, OpenApiParameter.PATH)]
        )
        @action(detail=False, url_path='callback/(?P<ephemeral>[^/.]+)', methods=['POST'])
        def callback(self, request, ephemeral, pk):
            return Response(status=201)  # pragma: no cover

        @extend_schema(responses={204: None})
        @action(detail=False, url_path='only-response-override', methods=['POST'])
        def only_response_override(self, request):
            return Response(status=201)  # pragma: no cover

        @extend_schema(parameters=[
            QuerySerializer,  # exploded
            OpenApiParameter('nested', QuerySerializer)  # nested
        ])
        @action(detail=False, url_path='serializer-query', methods=['GET'])
        def serializer_query(self, request):
            return Response([])  # pragma: no cover

        # this is intended as a measure of last resort when nothing else works
        @extend_schema(operation={
            "operationId": "manual_endpoint",
            "description": "fallback mechanism where can go all out",
            "tags": ["manual_tag"],
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/Alpha"}
                    },
                }
            },
            "deprecated": True,
            "responses": {
                "200": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Gamma"}
                        }
                    },
                    "description": ""
                },
            }
        })
        @action(detail=False, methods=['POST'])
        def manual(self, request):
            return Response()  # pragma: no cover

        @extend_schema(request=DeltaSerializer)
        @action(detail=False, methods=['POST'])
        def non_required_body(self, request):
            return Response([])  # pragma: no cover

        @extend_schema(responses={
            (200, 'application/pdf'): bytes
        })
        @action(detail=False, methods=['GET'])
        def document(self, request):
            return Response(b'deadbeef', status=200)  # pragma: no cover


def test_extend_schema(no_warnings):
    assert_schema(
        generate_schema('doesitall', DoesItAllViewset),
        'tests/test_extend_schema.yml'
    )


def test_layered_extend_schema_on_view_and_method_with_meta(no_warnings):
    class XSerializer(serializers.Serializer):
        field = serializers.IntegerField()

    @extend_schema(tags=['view_tag2'])
    @extend_schema(tags=['view_tag'], description='view_desc', summary='view_sum')
    class XViewset(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
        serializer_class = XSerializer

        @extend_schema(tags=['create_tag2'])
        @extend_schema(tags=['create_tag'], description='create_desc')
        def create(self, request, *args, **kwargs):
            super().create(request, *args, **kwargs)  # pragma: no cover

        @extend_schema(tags=['extended_action_tag2'])
        @extend_schema(tags=['extended_action_tag'], description='extended_action_desc')
        @action(detail=False, methods=['GET'])
        def extended_action(self, request):
            return Response()  # pragma: no cover

        @action(detail=False, methods=['GET'])
        def raw_action(self, request):
            return Response()  # pragma: no cover

    schema = generate_schema('x', XViewset)
    create_op = schema['paths']['/x/']['post']
    list_op = schema['paths']['/x/']['get']
    raw_action_op = schema['paths']['/x/raw_action/']['get']
    extended_action_op = schema['paths']['/x/extended_action/']['get']

    assert create_op['tags'][0] == 'create_tag2'
    assert create_op['description'] == 'create_desc'
    assert create_op['summary'] == 'view_sum'

    assert list_op['tags'][0] == 'view_tag2'
    assert list_op['description'] == 'view_desc'
    assert list_op['summary'] == 'view_sum'

    assert raw_action_op['tags'][0] == 'view_tag2'
    assert raw_action_op['description'] == 'view_desc'
    assert raw_action_op['summary'] == 'view_sum'

    assert extended_action_op['tags'][0] == 'extended_action_tag2'
    assert extended_action_op['description'] == 'extended_action_desc'
    assert extended_action_op['summary'] == 'view_sum'


def test_layered_extend_schema_on_view_and_method_with_serializer(no_warnings):
    class ASerializer(serializers.Serializer):
        field = serializers.IntegerField()

    class BSerializer(serializers.Serializer):
        field = serializers.IntegerField()

    class CSerializer(serializers.Serializer):
        field = serializers.IntegerField()

    @extend_schema(responses=BSerializer)
    class XViewset(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
        serializer_class = ASerializer

        @extend_schema(responses=CSerializer)
        def create(self, request, *args, **kwargs):
            super().create(request, *args, **kwargs)  # pragma: no cover

        @extend_schema(responses=CSerializer)
        @action(detail=False, methods=['GET'])
        def extended_action(self, request):
            return Response()  # pragma: no cover

        @action(detail=False, methods=['GET'])
        def raw_action(self, request):
            return Response()  # pragma: no cover

    schema = generate_schema('x', XViewset)
    create_op = get_response_schema(schema['paths']['/x/']['post'])
    list_op = get_response_schema(schema['paths']['/x/']['get'])
    raw_action_op = get_response_schema(schema['paths']['/x/raw_action/']['get'])
    extended_action_op = get_response_schema(schema['paths']['/x/extended_action/']['get'])

    assert create_op['$ref'].endswith('C')
    assert extended_action_op['$ref'].endswith('C')
    assert list_op['items']['$ref'].endswith('B')
    assert raw_action_op['$ref'].endswith('B')
