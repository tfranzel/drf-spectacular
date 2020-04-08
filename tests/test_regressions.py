from unittest import mock

from django.conf.urls import url
from django.db import models
from rest_framework import serializers, viewsets, mixins, routers
from rest_framework.views import APIView

from drf_spectacular.openapi import SchemaGenerator
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from drf_spectacular.validation import validate_schema
from tests import generate_schema


def test_primary_key_read_only_queryset_not_found(no_warnings):
    # the culprit - looks like a feature not a bug.
    # https://github.com/encode/django-rest-framework/blame/4d9f9eb192c5c1ffe4fa9210b90b9adbb00c3fdd/rest_framework/utils/field_mapping.py#L271

    class M1(models.Model):
        pass  # pragma: no cover

    class M2(models.Model):
        m1_r = models.ForeignKey(M1, on_delete=models.CASCADE)
        m1_rw = models.ForeignKey(M1, on_delete=models.CASCADE)

    class M2Serializer(serializers.ModelSerializer):
        class Meta:
            fields = ['m1_rw', 'm1_r']
            read_only_fields = ['m1_r']  # this produces the bug
            model = M2

    class M2Viewset(viewsets.ReadOnlyModelViewSet):
        serializer_class = M2Serializer
        queryset = M2.objects.none()

    schema = generate_schema('m2', M2Viewset)
    validate_schema(schema)
    props = schema['components']['schemas']['M2']['properties']
    assert props['m1_rw']['type'] == 'integer'
    assert props['m1_r']['type'] == 'integer'


def test_path_implicit_required(no_warnings):
    class M2Serializer(serializers.Serializer):
        pass  # pragma: no cover

    class M2Viewset(viewsets.GenericViewSet):
        serializer_class = M2Serializer

        @extend_schema(parameters=[OpenApiParameter('id', str, 'path')])
        def retrieve(self, request, *args, **kwargs):
            pass  # pragma: no cover

    schema = generate_schema('m2', M2Viewset)
    validate_schema(schema)


def test_free_form_responses(no_warnings):
    class XAPIView(APIView):
        @extend_schema(responses={200: OpenApiTypes.OBJECT})
        def get(self, request):
            pass  # pragma: no cover

    class YAPIView(APIView):
        @extend_schema(responses=OpenApiTypes.OBJECT)
        def get(self, request):
            pass  # pragma: no cover

    generator = SchemaGenerator(patterns=[
        url(r'^x$', XAPIView.as_view(), name='x'),
        url(r'^y$', YAPIView.as_view(), name='y'),
    ])
    schema = generator.get_schema(request=None, public=True)
    validate_schema(schema)


@mock.patch(
    target='drf_spectacular.settings.spectacular_settings.APPEND_COMPONENTS',
    new={'schemas': {'SomeExtraComponent': {'type': 'integer'}}}
)
def test_append_extra_components(no_warnings):
    class XSerializer(serializers.Serializer):
        id = serializers.UUIDField()

    class XAPIView(APIView):
        @extend_schema(responses={200: XSerializer})
        def get(self, request):
            pass  # pragma: no cover

    generator = SchemaGenerator(patterns=[
        url(r'^x$', XAPIView.as_view(), name='x'),
    ])
    schema = generator.get_schema(request=None, public=True)
    assert len(schema['components']['schemas']) == 2
    validate_schema(schema)


def test_serializer_retrieval_from_view(no_warnings):
    class UnusedSerializer(serializers.Serializer):
        pass  # pragma: no cover

    class XSerializer(serializers.Serializer):
        id = serializers.UUIDField()

    class YSerializer(serializers.Serializer):
        id = serializers.UUIDField()

    class X1Viewset(mixins.ListModelMixin, viewsets.GenericViewSet):
        serializer_class = UnusedSerializer

        def get_serializer(self):
            return XSerializer()

    class X2Viewset(mixins.ListModelMixin, viewsets.GenericViewSet):
        def get_serializer_class(self):
            return YSerializer

    router = routers.SimpleRouter()
    router.register('x1', X1Viewset, basename='x1')
    router.register('x2', X2Viewset, basename='x2')
    generator = SchemaGenerator(patterns=router.urls)
    schema = generator.get_schema(request=None, public=True)
    validate_schema(schema)
    assert len(schema['components']['schemas']) == 2
    assert 'Unused' not in schema['components']['schemas']


def test_retrieve_on_apiview_get(no_warnings):
    class XSerializer(serializers.Serializer):
        id = serializers.UUIDField()

    class XApiView(APIView):
        authentication_classes = []

        @extend_schema(
            parameters=[OpenApiParameter('id', OpenApiTypes.INT, OpenApiParameter.PATH)],
            responses={200: XSerializer},
        )
        def get(self, request):
            pass  # pragma: no cover

    schema = generate_schema('x', view=XApiView)
    operation = schema['paths']['/x']['get']
    assert operation['operationId'] == 'x_retrieve'
    operation_schema = operation['responses']['200']['content']['application/json']['schema']
    assert '$ref' in operation_schema and 'type' not in operation_schema

def test_list_on_apiview_get(no_warnings):
    class XSerializer(serializers.Serializer):
        id = serializers.UUIDField()

    class XApiView(APIView):
        authentication_classes = []

        @extend_schema(
            parameters=[OpenApiParameter('id', OpenApiTypes.INT, OpenApiParameter.PATH)],
            responses={200: XSerializer(many=True)},
        )
        def get(self, request):
            pass  # pragma: no cover

    schema = generate_schema('x', view=XApiView)
    operation = schema['paths']['/x']['get']
    assert operation['operationId'] == 'x_list'
    operation_schema = operation['responses']['200']['content']['application/json']['schema']
    assert operation_schema['type'] == 'array'