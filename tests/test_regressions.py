import datetime
import re
import typing
import uuid
from decimal import Decimal
from functools import partialmethod
from unittest import mock

import pytest
from django import __version__ as DJANGO_VERSION
from django.core import validators
from django.db import models
from django.db.models import fields
from django.urls import path, re_path, register_converter
from django.urls.converters import StringConverter
from rest_framework import (
    filters, generics, mixins, pagination, parsers, renderers, routers, serializers, views,
    viewsets,
)
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.decorators import action, api_view
from rest_framework.views import APIView

from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.hooks import preprocess_exclude_path_format
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.renderers import OpenApiJsonRenderer, OpenApiYamlRenderer
from drf_spectacular.settings import IMPORT_STRINGS, SPECTACULAR_DEFAULTS
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_field,
    extend_schema_serializer, extend_schema_view, inline_serializer,
)
from tests import generate_schema, get_request_schema, get_response_schema
from tests.models import SimpleModel, SimpleSerializer


def test_primary_key_read_only_queryset_not_found(no_warnings):
    # the culprit - looks like a feature not a bug.
    # https://github.com/encode/django-rest-framework/blame/4d9f9eb192c5c1ffe4fa9210b90b9adbb00c3fdd/rest_framework/utils/field_mapping.py#L271

    class M1(models.Model):
        pass  # pragma: no cover

    class M2(models.Model):
        id = models.UUIDField()
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
    props = schema['components']['schemas']['M2']['properties']
    assert props['m1_rw']['type'] == 'integer'
    assert props['m1_r']['type'] == 'integer'


def test_multi_step_serializer_primary_key_related_field(no_warnings):
    class MA1(models.Model):
        id = models.UUIDField(primary_key=True)

    class MA2(models.Model):
        m1 = models.ForeignKey(MA1, on_delete=models.CASCADE)

    class MA3(models.Model):
        m2 = models.ForeignKey(MA2, on_delete=models.CASCADE)

    class M3Serializer(serializers.ModelSerializer):
        # this scenario looks explicitly at multi-step sources with read_only=True
        m1 = serializers.PrimaryKeyRelatedField(source='m2.m1', required=False, read_only=True)

        class Meta:
            fields = ['m1', 'm2']
            model = MA3

    class M3Viewset(viewsets.ReadOnlyModelViewSet):
        serializer_class = M3Serializer
        queryset = MA3.objects.none()

    schema = generate_schema('m3', M3Viewset)
    properties = schema['components']['schemas']['M3']['properties']
    assert properties['m1']['format'] == 'uuid'
    assert properties['m2']['type'] == 'integer'


def test_serializer_reverse_relations_including_read_only(no_warnings):
    class M5(models.Model):
        pass

    class M5One(models.Model):
        id = models.CharField(primary_key=True, max_length=10)
        field = models.OneToOneField(M5, on_delete=models.CASCADE)

    class M5Many(models.Model):
        id = models.UUIDField(primary_key=True, default=uuid.uuid4)
        field = models.ManyToManyField(M5)

    class M5Foreign(models.Model):
        id = models.FloatField(primary_key=True)
        field = models.ForeignKey(M5, on_delete=models.CASCADE)

    class XSerializer(serializers.ModelSerializer):
        m5foreign_set_explicit = serializers.PrimaryKeyRelatedField(
            many=True, source='m5foreign_set', queryset=M5Foreign.objects.all()
        )
        m5foreign_set_ro = serializers.PrimaryKeyRelatedField(
            many=True, source='m5foreign_set', read_only=True,
        )
        m5many_set_explicit = serializers.PrimaryKeyRelatedField(
            many=True, source='m5many_set', queryset=M5Many.objects.all()
        )
        m5many_set_ro = serializers.PrimaryKeyRelatedField(
            many=True, source='m5many_set', read_only=True,
        )
        m5one_ro = serializers.PrimaryKeyRelatedField(
            source='m5one', read_only=True,
        )

        class Meta:
            model = M5
            fields = [
                'm5many_set',
                'm5many_set_explicit',
                'm5many_set_ro',
                'm5foreign_set',
                'm5foreign_set_explicit',
                'm5foreign_set_ro',
                'm5one',
                'm5one_ro',
            ]

    class TestViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
        queryset = M5.objects.all()
        serializer_class = XSerializer

    schema = generate_schema('/x/', TestViewSet)
    properties = schema['components']['schemas']['X']['properties']

    m5many_pk = {'type': 'string', 'format': 'uuid'}
    assert properties['m5many_set']['items'] == m5many_pk
    assert properties['m5many_set_ro']['items'] == m5many_pk
    assert properties['m5many_set_explicit']['items'] == m5many_pk

    m5foreign_pk = {'type': 'number', 'format': 'float'}
    assert properties['m5foreign_set']['items'] == m5foreign_pk
    assert properties['m5foreign_set_ro']['items'] == m5foreign_pk
    assert properties['m5foreign_set_explicit']['items'] == m5foreign_pk

    assert properties['m5one'] == {'type': 'string'}
    assert properties['m5one_ro'] == {'readOnly': True, 'type': 'string'}


def test_serializer_forward_relations_including_read_only(no_warnings):
    class M6One(models.Model):
        id = models.CharField(primary_key=True, max_length=10)

    class M6Many(models.Model):
        id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    class M6Foreign(models.Model):
        id = models.FloatField(primary_key=True)

    class M6(models.Model):
        field_one = models.OneToOneField(M6One, on_delete=models.CASCADE)
        field_many = models.ManyToManyField(M6Many)
        field_foreign = models.ForeignKey(M6Foreign, on_delete=models.CASCADE)

    class XSerializer(serializers.ModelSerializer):
        field_one_ro = serializers.PrimaryKeyRelatedField(
            source='field_one', read_only=True
        )
        field_foreign_ro = serializers.PrimaryKeyRelatedField(
            source='field_foreign', read_only=True
        )
        field_many_ro = serializers.PrimaryKeyRelatedField(
            source='field_many', read_only=True, many=True
        )

        class Meta:
            model = M6
            fields = [
                'field_one',
                'field_one_ro',
                'field_many',
                'field_many_ro',
                'field_foreign',
                'field_foreign_ro',
            ]

    class TestViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
        queryset = M6.objects.all()
        serializer_class = XSerializer

    schema = generate_schema('/x/', TestViewSet)
    properties = schema['components']['schemas']['X']['properties']

    assert properties['field_one'] == {'type': 'string'}
    assert properties['field_one_ro'] == {'type': 'string', 'readOnly': True}
    assert properties['field_foreign'] == {'type': 'number', 'format': 'float'}
    assert properties['field_foreign_ro'] == {'type': 'number', 'format': 'float', 'readOnly': True}
    assert properties['field_many'] == {'type': 'array', 'items': {'type': 'string', 'format': 'uuid'}}
    assert properties['field_many_ro'] == {
        'type': 'array', 'items': {'type': 'string', 'format': 'uuid'}, 'readOnly': True
    }


def test_path_implicit_required(no_warnings):
    class M2Serializer(serializers.Serializer):
        pass  # pragma: no cover

    class M2Viewset(viewsets.GenericViewSet):
        serializer_class = M2Serializer

        @extend_schema(parameters=[OpenApiParameter('id', str, 'path')])
        def retrieve(self, request, *args, **kwargs):
            pass  # pragma: no cover

    generate_schema('m2', M2Viewset)


def test_free_form_responses(no_warnings):
    class XAPIView(APIView):
        @extend_schema(responses={200: OpenApiTypes.OBJECT})
        def get(self, request):
            pass  # pragma: no cover

    class YAPIView(APIView):
        @extend_schema(responses=OpenApiTypes.OBJECT)
        def get(self, request):
            pass  # pragma: no cover

    generate_schema(None, patterns=[
        re_path(r'^x$', XAPIView.as_view(), name='x'),
        re_path(r'^y$', YAPIView.as_view(), name='y'),
    ])


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

    schema = generate_schema(None, patterns=[
        re_path(r'^x$', XAPIView.as_view(), name='x'),
    ])
    assert len(schema['components']['schemas']) == 2


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
    schema = generate_schema(None, patterns=router.urls)
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
    operation_schema = get_response_schema(operation)
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
    operation_schema = get_response_schema(operation)
    assert operation_schema['type'] == 'array'


def test_multi_method_action(no_warnings):
    class DummySerializer(serializers.Serializer):
        id = serializers.UUIDField()

    class UpdateSerializer(serializers.Serializer):
        id = serializers.UUIDField()

    class CreateSerializer(serializers.Serializer):
        id = serializers.UUIDField()

    class XViewset(viewsets.GenericViewSet):
        serializer_class = DummySerializer

        # basic usage
        @extend_schema(request=UpdateSerializer, methods=['PUT'])
        @extend_schema(request=CreateSerializer, methods=['POST'])
        @action(detail=False, methods=['PUT', 'POST'])
        def multi(self, request, *args, **kwargs):
            pass  # pragma: no cover

        # bolt-on decorator variation
        @extend_schema(request=CreateSerializer)
        @action(detail=False, methods=['POST'])
        def multi2(self, request, *args, **kwargs):
            pass  # pragma: no cover

        @extend_schema(request=UpdateSerializer)
        @multi2.mapping.put
        def multi2put(self, request, *args, **kwargs):
            pass  # pragma: no cover

    schema = generate_schema('x', XViewset)

    def get_req_body(s):
        return s['requestBody']['content']['application/json']['schema']['$ref']

    assert get_req_body(schema['paths']['/x/multi/']['put']) == '#/components/schemas/Update'
    assert get_req_body(schema['paths']['/x/multi/']['post']) == '#/components/schemas/Create'

    assert get_req_body(schema['paths']['/x/multi2/']['put']) == '#/components/schemas/Update'
    assert get_req_body(schema['paths']['/x/multi2/']['post']) == '#/components/schemas/Create'


def test_serializer_class_on_apiview(no_warnings):
    class XSerializer(serializers.Serializer):
        field = serializers.UUIDField()

    class XView(views.APIView):
        serializer_class = XSerializer  # not supported by DRF but pick it up anyway

        def get(self, request):
            pass  # pragma: no cover

        def post(self, request):
            pass  # pragma: no cover

    schema = generate_schema('x', view=XView)
    comp = '#/components/schemas/X'
    assert get_response_schema(schema['paths']['/x']['get'])['$ref'] == comp
    assert get_response_schema(schema['paths']['/x']['post'])['$ref'] == comp
    assert schema['paths']['/x']['post']['requestBody']['content']['application/json']['schema']['$ref'] == comp


def test_customized_list_serializer():
    class X(models.Model):
        position = models.IntegerField()

    class XSerializer(serializers.ModelSerializer):
        class Meta:
            model = X
            fields = ("id", "position")

    class XListUpdateSerializer(serializers.ListSerializer):
        child = XSerializer()

    class XAPIView(generics.GenericAPIView):
        model = X
        serializer_class = XListUpdateSerializer

        def put(self, request, *args, **kwargs):
            pass  # pragma: no cover

    schema = generate_schema('x', view=XAPIView)
    operation = schema['paths']['/x']['put']
    comp = '#/components/schemas/X'

    assert get_request_schema(operation)['type'] == 'array'
    assert get_request_schema(operation)['items']['$ref'] == comp
    assert get_response_schema(operation)['type'] == 'array'
    assert get_response_schema(operation)['items']['$ref'] == comp

    assert operation['operationId'] == 'x_update'
    assert len(schema['components']['schemas']) == 1 and 'X' in schema['components']['schemas']


def test_api_view_decorator(no_warnings):

    @extend_schema(responses=OpenApiTypes.FLOAT)
    @api_view(['GET'])
    def pi(request):
        pass  # pragma: no cover

    schema = generate_schema('x', view_function=pi)
    operation = schema['paths']['/x']['get']
    assert get_response_schema(operation)['type'] == 'number'


def test_api_view_decorator_multi(no_warnings):

    @extend_schema(request=OpenApiTypes.FLOAT, responses=OpenApiTypes.INT, methods=['POST'])
    @extend_schema(responses=OpenApiTypes.FLOAT, methods=['GET'])
    @api_view(['GET', 'POST'])
    def pi(request):
        pass  # pragma: no cover

    schema = generate_schema('x', view_function=pi)
    operation = schema['paths']['/x']['get']
    assert get_response_schema(operation)['type'] == 'number'
    operation = schema['paths']['/x']['post']
    assert get_request_schema(operation)['type'] == 'number'
    assert get_response_schema(operation)['type'] == 'integer'


def test_pk_and_no_id(no_warnings):
    class XModel(models.Model):
        id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class YModel(models.Model):
        x = models.OneToOneField(XModel, primary_key=True, on_delete=models.CASCADE)

    class YSerializer(serializers.ModelSerializer):
        class Meta:
            model = YModel
            fields = '__all__'

    class YViewSet(viewsets.ReadOnlyModelViewSet):
        serializer_class = YSerializer
        queryset = YModel.objects.all()

    schema = generate_schema('y', YViewSet)
    assert schema['components']['schemas']['Y']['properties']['x']['format'] == 'uuid'


@pytest.mark.parametrize('allowed', [None, ['json', 'NoRendererAvailable']])
def test_drf_format_suffix_parameter(no_warnings, allowed):
    from rest_framework.urlpatterns import format_suffix_patterns

    @extend_schema(responses=OpenApiTypes.FLOAT)
    @api_view(['GET'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    urlpatterns = [
        path('pi/', view_func),
        path('pi/subpath', view_func),
        path('pick', view_func),
    ]
    urlpatterns = format_suffix_patterns(urlpatterns, allowed=allowed)

    schema = generate_schema(None, patterns=urlpatterns)

    # Only seven alternatives are created, as /pi/{format} would be
    # /pi/.json which is not supported.
    assert list(schema['paths'].keys()) == [
        '/pi/',
        '/pi{format}',
        '/pi/subpath',
        '/pi/subpath{format}',
        '/pick',
        '/pick{format}',
    ]
    assert schema['paths']['/pi/']['get']['operationId'] == 'pi_retrieve'
    assert schema['paths']['/pi{format}']['get']['operationId'] == 'pi_formatted_retrieve'

    format_parameter = schema['paths']['/pi{format}']['get']['parameters'][0]
    assert format_parameter['name'] == 'format'
    assert format_parameter['required'] is True
    assert format_parameter['in'] == 'path'
    assert format_parameter['schema']['type'] == 'string'
    # When allowed is not specified, all of the default formats are possible.
    # Even if other values are provided, only the valid formats are possible.
    assert format_parameter['schema']['enum'] == ['.json']


@mock.patch(
    'drf_spectacular.settings.spectacular_settings.PREPROCESSING_HOOKS',
    [preprocess_exclude_path_format]
)
def test_drf_format_suffix_parameter_exclude(no_warnings):
    from rest_framework.urlpatterns import format_suffix_patterns

    @extend_schema(responses=OpenApiTypes.FLOAT)
    @api_view(['GET'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    urlpatterns = format_suffix_patterns([
        path('pi', view_func),
    ])
    schema = generate_schema(None, patterns=urlpatterns)
    assert list(schema['paths'].keys()) == ['/pi']


def test_regex_path_parameter_discovery(no_warnings):
    @extend_schema(responses=OpenApiTypes.FLOAT)
    @api_view(['GET'])
    def pi(request, foo):
        pass  # pragma: no cover

    urlpatterns = [re_path(r'^/pi/<int:precision>', pi)]
    schema = generate_schema(None, patterns=urlpatterns)
    parameter = schema['paths']['/pi/{precision}']['get']['parameters'][0]
    assert parameter['name'] == 'precision'
    assert parameter['in'] == 'path'
    assert parameter['schema']['type'] == 'integer'


def test_lib_serializer_naming_collision_resolution(no_warnings):
    """ parity test in tests.test_warnings.test_serializer_name_reuse """
    def x_lib1():
        class XSerializer(serializers.Serializer):
            x = serializers.UUIDField()

        return XSerializer

    def x_lib2():
        class XSerializer(serializers.Serializer):
            x = serializers.IntegerField()

        return XSerializer

    x_lib1, x_lib2 = x_lib1(), x_lib2()

    class XAPIView(APIView):
        @extend_schema(request=x_lib1, responses=x_lib2)
        def post(self, request):
            pass  # pragma: no cover

    class Lib2XSerializerRename(OpenApiSerializerExtension):
        target_class = x_lib2  # also accepts import strings

        def get_name(self):
            return 'RenamedLib2X'

    schema = generate_schema('x', view=XAPIView)

    operation = schema['paths']['/x']['post']
    assert get_request_schema(operation)['$ref'] == '#/components/schemas/X'
    assert get_response_schema(operation)['$ref'] == '#/components/schemas/RenamedLib2X'


def test_owned_serializer_naming_override_with_ref_name(no_warnings):
    def x_owned1():
        class XSerializer(serializers.Serializer):
            x = serializers.UUIDField()

        return XSerializer

    def x_owned2():
        class XSerializer(serializers.Serializer):
            x = serializers.IntegerField()

            class Meta:
                ref_name = 'Y'

        return XSerializer

    x_owned1, x_owned2 = x_owned1(), x_owned2()

    class XAPIView(APIView):
        @extend_schema(request=x_owned1, responses=x_owned2)
        def post(self, request):
            pass  # pragma: no cover

    schema = generate_schema('x', view=XAPIView)

    operation = schema['paths']['/x']['post']
    assert get_request_schema(operation)['$ref'] == '#/components/schemas/X'
    assert get_response_schema(operation)['$ref'] == '#/components/schemas/Y'


def test_custom_model_field_from_typed_field(no_warnings):
    class CustomIntegerField(fields.IntegerField):
        pass  # pragma: no cover

    class CustomTypedFieldModel(models.Model):
        custom_int_field = CustomIntegerField()

    class XSerializer(serializers.ModelSerializer):
        class Meta:
            model = CustomTypedFieldModel
            fields = '__all__'

    class XAPIView(APIView):
        @extend_schema(responses=XSerializer)
        def get(self, request):
            pass  # pragma: no cover

    schema = generate_schema('x', view=XAPIView)
    component = schema['components']['schemas']['X']
    assert component['properties']['custom_int_field']['type'] == 'integer'


def test_custom_model_field_from_base_field(no_warnings):
    class CustomIntegerField(fields.Field):
        def get_internal_type(self):
            return 'IntegerField'

    class CustomBaseFieldModel(models.Model):
        custom_int_field = CustomIntegerField()

    class XSerializer(serializers.ModelSerializer):
        class Meta:
            model = CustomBaseFieldModel
            fields = '__all__'

    class XAPIView(APIView):
        @extend_schema(responses=XSerializer)
        def get(self, request):
            pass  # pragma: no cover

    schema = generate_schema('x', view=XAPIView)
    component = schema['components']['schemas']['X']
    assert component['properties']['custom_int_field']['type'] == 'integer'


def test_follow_field_source_through_intermediate_property_or_function(no_warnings):
    class FieldSourceTraversalModel2(models.Model):
        x = models.IntegerField(choices=[(1, '1'), (2, '2')])
        y = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3')])

    class FieldSourceTraversalModel1(models.Model):
        @property
        def prop(self) -> FieldSourceTraversalModel2:  # property is required for traversal
            return  # type: ignore # pragma: no cover

        def func(self) -> FieldSourceTraversalModel2:  # property is required for traversal
            return  # type: ignore # pragma: no cover

    class XSerializer(serializers.ModelSerializer):
        prop = serializers.ReadOnlyField(source='prop.x')
        func = serializers.ReadOnlyField(source='func.y')

        class Meta:
            model = FieldSourceTraversalModel1
            fields = '__all__'

    class XAPIView(APIView):
        @extend_schema(responses=XSerializer)
        def get(self, request):
            pass  # pragma: no cover

    # this checks if field type is correctly estimated AND field was initialized
    # with the model parameters (choices)
    schema = generate_schema('x', view=XAPIView)
    assert schema['components']['schemas']['X']['properties']['func']['readOnly'] is True
    assert schema['components']['schemas']['X']['properties']['prop']['readOnly'] is True
    assert 'enum' in schema['components']['schemas']['PropEnum']
    assert 'enum' in schema['components']['schemas']['FuncEnum']
    assert schema['components']['schemas']['PropEnum']['type'] == 'integer'
    assert schema['components']['schemas']['FuncEnum']['type'] == 'integer'


def test_viewset_list_with_envelope(no_warnings):
    class XSerializer(serializers.Serializer):
        x = serializers.IntegerField()

    def enveloper(serializer_class, many):
        component_name = 'Enveloped{}{}'.format(
            serializer_class.__name__.replace("Serializer", ""),
            "List" if many else "",
        )

        @extend_schema_serializer(many=False, component_name=component_name)
        class EnvelopeSerializer(serializers.Serializer):
            status = serializers.BooleanField()
            data = serializer_class(many=many)

        return EnvelopeSerializer

    class XViewset(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
        @extend_schema(responses=enveloper(XSerializer, True))
        def list(self, request, *args, **kwargs):
            return super().list(request, *args, **kwargs)  # pragma: no cover

        @extend_schema(
            responses=enveloper(XSerializer, False),
            parameters=[OpenApiParameter('id', int, OpenApiParameter.PATH)],
        )
        def retrieve(self, request, *args, **kwargs):
            return super().retrieve(request, *args, **kwargs)  # pragma: no cover

    schema = generate_schema('x', viewset=XViewset)

    operation_list = schema['paths']['/x/']['get']
    assert operation_list['operationId'] == 'x_list'
    assert get_response_schema(operation_list)['$ref'] == '#/components/schemas/EnvelopedXList'

    operation_retrieve = schema['paths']['/x/{id}/']['get']
    assert operation_retrieve['operationId'] == 'x_retrieve'
    assert get_response_schema(operation_retrieve)['$ref'] == '#/components/schemas/EnvelopedX'


@mock.patch('drf_spectacular.settings.spectacular_settings.COMPONENT_SPLIT_REQUEST', True)
def test_component_split_request():
    class XSerializer(serializers.Serializer):
        ro = serializers.IntegerField(read_only=True)
        rw = serializers.IntegerField()
        wo = serializers.IntegerField(write_only=True)

    @extend_schema(request=XSerializer, responses=XSerializer)
    @api_view(['POST'])
    def pi(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('/x', view_function=pi)

    operation = schema['paths']['/x']['post']

    assert get_response_schema(operation)['$ref'] == '#/components/schemas/X'
    assert get_request_schema(operation)['$ref'] == '#/components/schemas/XRequest'
    assert len(schema['components']['schemas']['X']['properties']) == 2
    assert 'wo' not in schema['components']['schemas']['X']['properties']
    assert len(schema['components']['schemas']['XRequest']['properties']) == 2
    assert 'ro' not in schema['components']['schemas']['XRequest']['properties']


def test_list_api_view(no_warnings):
    class XSerializer(serializers.Serializer):
        id = serializers.IntegerField()

    class XView(generics.ListAPIView):
        serializer_class = XSerializer

    schema = generate_schema('/x', view=XView)
    operation = schema['paths']['/x']['get']
    assert operation['operationId'] == 'x_list'
    assert get_response_schema(operation)['type'] == 'array'


@mock.patch('drf_spectacular.settings.spectacular_settings.COMPONENT_SPLIT_REQUEST', True)
def test_file_field_duality_on_split_request(no_warnings):
    class XSerializer(serializers.Serializer):
        file = serializers.FileField()

    class XView(generics.ListCreateAPIView):
        serializer_class = XSerializer
        parser_classes = [parsers.MultiPartParser]

    schema = generate_schema('/x', view=XView)
    assert get_response_schema(
        schema['paths']['/x']['get']
    )['items']['$ref'] == '#/components/schemas/X'
    assert get_request_schema(
        schema['paths']['/x']['post'], content_type='multipart/form-data'
    )['$ref'] == '#/components/schemas/XRequest'

    assert schema['components']['schemas']['X']['properties']['file']['format'] == 'uri'
    assert schema['components']['schemas']['XRequest']['properties']['file']['format'] == 'binary'


@mock.patch('drf_spectacular.settings.spectacular_settings.COMPONENT_SPLIT_REQUEST', True)
def test_component_split_nested_ro_wo_serializer(no_warnings):
    class RoSerializer(serializers.Serializer):
        ro_field = serializers.IntegerField(read_only=True)

    class WoSerializer(serializers.Serializer):
        wo_field = serializers.IntegerField(write_only=True)

    class XSerializer(serializers.Serializer):
        ro = RoSerializer()
        wo = WoSerializer()

    class XView(generics.ListCreateAPIView):
        serializer_class = XSerializer

    schema = generate_schema('/x', view=XView)
    assert 'RoRequest' not in schema['components']['schemas']
    assert 'Wo' not in schema['components']['schemas']
    assert len(schema['components']['schemas']['X']['properties']) == 1
    assert len(schema['components']['schemas']['XRequest']['properties']) == 1


@mock.patch('drf_spectacular.settings.spectacular_settings.COMPONENT_SPLIT_REQUEST', True)
def test_component_split_nested_explicit_ro_wo_serializer(no_warnings):
    class NestedSerializer(serializers.Serializer):
        field = serializers.IntegerField()

    class XSerializer(serializers.Serializer):
        ro = NestedSerializer(read_only=True)
        wo = NestedSerializer(write_only=True, required=False)

    class XView(generics.ListCreateAPIView):
        serializer_class = XSerializer

    schema = generate_schema('/x', view=XView)
    assert 'NestedRequest' in schema['components']['schemas']
    assert 'Nested' in schema['components']['schemas']
    assert len(schema['components']['schemas']['X']['properties']) == 1
    assert len(schema['components']['schemas']['XRequest']['properties']) == 1


def test_read_only_many_related_field(no_warnings):
    class ManyRelatedTargetModel(models.Model):
        field = models.IntegerField()

    class ManyRelatedModel(models.Model):
        field_m2m = models.ManyToManyField(ManyRelatedTargetModel)
        field_m2m_ro = models.ManyToManyField(ManyRelatedTargetModel)

    class XSerializer(serializers.ModelSerializer):
        class Meta:
            model = ManyRelatedModel
            fields = '__all__'
            read_only_fields = ['field_m2m_ro']

    class XAPIView(APIView):
        @extend_schema(responses=XSerializer)
        def get(self, request):
            pass  # pragma: no cover

    schema = generate_schema('x', view=XAPIView)
    properties = schema['components']['schemas']['X']['properties']
    # readOnly only needed on outer object, not in items
    assert properties['field_m2m'] == {'type': 'array', 'items': {'type': 'integer'}}
    assert properties['field_m2m_ro'] == {
        'type': 'array', 'items': {'type': 'integer'}, 'readOnly': True
    }


def test_extension_subclass_discovery(no_warnings):
    from rest_framework.authentication import TokenAuthentication

    class CustomAuth(TokenAuthentication):
        pass

    class XSerializer(serializers.Serializer):
        field = serializers.IntegerField()

    class XAPIView(APIView):
        authentication_classes = [CustomAuth]

        @extend_schema(responses=XSerializer)
        def get(self, request):
            pass  # pragma: no cover

    generate_schema('x', view=XAPIView)


def test_extend_schema_no_req_no_res(no_warnings):
    class XAPIView(APIView):
        @extend_schema(request=None, responses=None)
        def post(self, request):
            pass  # pragma: no cover

    schema = generate_schema('/x', view=XAPIView)
    operation = schema['paths']['/x']['post']
    assert 'requestBody' not in operation
    assert len(operation['responses']['200']) == 1
    assert 'description' in operation['responses']['200']


def test_extend_schema_field_exclusion(no_warnings):
    @extend_schema_field(None)
    class CustomField(serializers.IntegerField):
        pass  # pragma: no cover

    class XSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        hidden = CustomField()

    class XView(generics.CreateAPIView):
        serializer_class = XSerializer

    schema = generate_schema('/x', view=XView)
    assert 'hidden' not in schema['components']['schemas']['X']['properties']


def test_extend_schema_serializer_field_exclusion(no_warnings):
    @extend_schema_serializer(exclude_fields=['hidden1', 'hidden2'])
    class XSerializer(serializers.Serializer):
        integer = serializers.IntegerField()
        hidden1 = serializers.IntegerField()
        hidden2 = serializers.CharField()

    class XView(generics.ListCreateAPIView):
        serializer_class = XSerializer

    schema = generate_schema('/x', view=XView)
    assert 'integer' in schema['components']['schemas']['X']['properties']
    assert 'hidden1' not in schema['components']['schemas']['X']['properties']
    assert 'hidden2' not in schema['components']['schemas']['X']['properties']


def test_schema_contains_only_urlpatterns_first_match(no_warnings):
    class XSerializer(serializers.Serializer):
        integer = serializers.IntegerField()

    class XAPIView(APIView):
        @extend_schema(responses=XSerializer)
        def get(self, request):
            pass  # pragma: no cover

    class YSerializer(serializers.Serializer):
        integer = serializers.DateTimeField()

    class YAPIView(APIView):
        @extend_schema(responses=YSerializer)
        def get(self, request):
            pass  # pragma: no cover

    urlpatterns = [
        path('api/x/', XAPIView.as_view()),  # only first occurrence is used
        path('api/x/', YAPIView.as_view()),
    ]
    schema = generate_schema(None, patterns=urlpatterns)
    assert len(schema['components']['schemas']) == 1
    assert 'X' in schema['components']['schemas']
    operation = schema['paths']['/api/x/']['get']
    assert '#/components/schemas/X' in get_response_schema(operation)['$ref']


def test_auto_schema_and_extend_parameters(no_warnings):
    class CustomAutoSchema(AutoSchema):
        def get_override_parameters(self):
            return [
                OpenApiParameter("id", str, OpenApiParameter.PATH),
                OpenApiParameter("foo", str, deprecated=True),
                OpenApiParameter("bar", str),
            ]

    class XSerializer(serializers.Serializer):
        id = serializers.IntegerField()

    with mock.patch('rest_framework.settings.api_settings.DEFAULT_SCHEMA_CLASS', CustomAutoSchema):
        class XViewSet(viewsets.GenericViewSet):
            serializer_class = XSerializer

            @extend_schema(parameters=[OpenApiParameter("bar", int)])
            def list(self, request, *args, **kwargs):
                pass  # pragma: no cover

        schema = generate_schema('x', XViewSet)

    parameters = schema['paths']['/x/']['get']['parameters']
    assert parameters[0]['name'] == 'bar' and parameters[0]['schema']['type'] == 'integer'
    assert parameters[1]['name'] == 'foo' and parameters[1]['schema']['type'] == 'string'
    assert parameters[1]['deprecated'] is True
    assert parameters[2]['name'] == 'id'


def test_manually_set_auto_schema_with_extend_schema(no_warnings):
    class CustomSchema(AutoSchema):
        def get_override_parameters(self):
            if self.method.lower() == "delete":
                return [OpenApiParameter("custom_param", str)]
            return super().get_override_parameters()

    @extend_schema_view(
        list=extend_schema(summary="list summary"),
        destroy=extend_schema(summary="delete summary"),
    )
    class XViewSet(mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.ViewSet):
        queryset = SimpleModel.objects.all()
        serializer_class = SimpleSerializer
        schema = CustomSchema()

    schema = generate_schema('x', XViewSet)
    assert schema['paths']['/x/']['get']['summary'] == 'list summary'
    assert schema['paths']['/x/{id}/']['delete']['summary'] == 'delete summary'
    assert schema['paths']['/x/{id}/']['delete']['parameters'][0]['name'] == 'custom_param'
    assert schema['paths']['/x/{id}/']['delete']['parameters'][1]['name'] == 'id'


def test_list_serializer_with_field_child():
    class XSerializer(serializers.Serializer):
        field = serializers.ListSerializer(child=serializers.IntegerField())

    class XAPIView(views.APIView):
        serializer_class = XSerializer

        def post(self, request, *args, **kwargs):
            pass  # pragma: no cover

    # assumption on Serializer functionality
    assert XSerializer({'field': [1, 2, 3]}).data['field'] == [1, 2, 3]

    schema = generate_schema('x', view=XAPIView)
    assert get_request_schema(schema['paths']['/x']['post'])['$ref'] == '#/components/schemas/X'
    assert get_response_schema(schema['paths']['/x']['post'])['$ref'] == '#/components/schemas/X'

    properties = schema['components']['schemas']['X']['properties']
    assert properties['field']['type'] == 'array'
    assert properties['field']['items']['type'] == 'integer'


def test_list_serializer_with_field_child_on_extend_schema(no_warnings):
    class XAPIView(APIView):
        @extend_schema(
            request=serializers.ListSerializer(child=serializers.IntegerField()),
            responses=serializers.ListSerializer(child=serializers.IntegerField()),
        )
        def post(self, request):
            pass  # pragma: no cover

    schema = generate_schema('x', view=XAPIView)
    req_schema = get_request_schema(schema['paths']['/x']['post'])
    res_schema = get_response_schema(schema['paths']['/x']['post'])
    for s in [req_schema, res_schema]:
        assert s['type'] == 'array'
        assert s['items']['type'] == 'integer'


def test_list_serializer_with_pagination(no_warnings):
    class GenreSerializer(serializers.Serializer):
        genre = serializers.CharField()

    class XViewSet(viewsets.GenericViewSet):
        pagination_class = pagination.LimitOffsetPagination

        @extend_schema(responses=GenreSerializer(many=True))
        @action(methods=["GET"], detail=False)
        def genre(self, request, *args, **kwargs):
            pass  # pragma: no cover

    schema = generate_schema('/x', XViewSet)
    response = get_response_schema(schema['paths']['/x/genre/']['get'])
    assert response['$ref'] == '#/components/schemas/PaginatedGenreList'
    assert 'PaginatedGenreList' in schema['components']['schemas']
    assert 'Genre' in schema['components']['schemas']


def test_inline_serializer(no_warnings):
    @extend_schema(
        responses=inline_serializer(
            name='InlineOneOffSerializer',
            fields={
                'char': serializers.CharField(),
                'choice': serializers.ChoiceField(choices=(('A', 'A'), ('B', 'B'))),
                'nested_inline': inline_serializer(
                    name='NestedInlineOneOffSerializer',
                    fields={
                        'char': serializers.CharField(),
                        'int': serializers.IntegerField(),
                    },
                    allow_null=True,
                )
            }
        )
    )
    @api_view(['GET'])
    def one_off(request, foo):
        pass  # pragma: no cover

    schema = generate_schema('x', view_function=one_off)
    assert get_response_schema(schema['paths']['/x']['get'])['$ref'] == (
        '#/components/schemas/InlineOneOff'
    )
    assert len(schema['components']['schemas']) == 3

    one_off = schema['components']['schemas']['InlineOneOff']
    one_off_nested = schema['components']['schemas']['NestedInlineOneOff']

    assert len(one_off['properties']) == 3
    assert one_off['properties']['nested_inline']['nullable'] is True
    assert one_off['properties']['nested_inline']['allOf'][0]['$ref'] == (
        '#/components/schemas/NestedInlineOneOff'
    )
    assert len(one_off_nested['properties']) == 2


@mock.patch('drf_spectacular.settings.spectacular_settings.CAMELIZE_NAMES', True)
def test_camelize_names(no_warnings):
    @extend_schema(responses=OpenApiTypes.FLOAT)
    @api_view(['GET'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('/multi/step/path/<str:some_name>/', view_function=view_func)
    operation = schema['paths']['/multi/step/path/{someName}/']['get']
    assert operation['parameters'][0]['name'] == 'someName'
    assert operation['operationId'] == 'multiStepPathRetrieve'


def test_mocked_request_with_get_queryset_get_serializer_class(no_warnings):
    class XViewset(viewsets.ReadOnlyModelViewSet):
        def get_serializer_class(self):
            assert not self.request.user.is_authenticated
            assert self.action in ['retrieve', 'list']
            assert getattr(self, 'swagger_fake_view', False)  # drf-yasg comp
            return SimpleSerializer

        def get_queryset(self):
            assert not self.request.user.is_authenticated
            assert self.request.method == 'GET'
            assert getattr(self, 'swagger_fake_view', False)  # drf-yasg comp
            return SimpleModel.objects.none()

    generate_schema('x', XViewset)


def test_queryset_filter_and_ordering_only_on_list(no_warnings):
    class XViewset(viewsets.ReadOnlyModelViewSet):
        queryset = SimpleModel.objects.none()
        serializer_class = SimpleSerializer
        filter_backends = (filters.SearchFilter, filters.OrderingFilter)

    schema = generate_schema('x', XViewset)

    retrieve_parameters = schema['paths']['/x/']['get']['parameters']
    assert len(retrieve_parameters) == 2
    assert retrieve_parameters[0]['name'] == 'ordering'
    assert retrieve_parameters[1]['name'] == 'search'

    list_parameters = schema['paths']['/x/{id}/']['get']['parameters']
    assert len(list_parameters) == 1
    assert list_parameters[0]['name'] == 'id'


def test_pagination(no_warnings):
    class XViewset(viewsets.ReadOnlyModelViewSet):
        queryset = SimpleModel.objects.none()
        serializer_class = SimpleSerializer
        pagination_class = pagination.LimitOffsetPagination

    schema = generate_schema('x', XViewset)

    # query params only on list
    retrieve_parameters = schema['paths']['/x/']['get']['parameters']
    assert len(retrieve_parameters) == 2
    assert retrieve_parameters[0]['name'] == 'limit'
    assert retrieve_parameters[1]['name'] == 'offset'

    # no query params on retrieve
    list_parameters = schema['paths']['/x/{id}/']['get']['parameters']
    assert len(list_parameters) == 1
    assert list_parameters[0]['name'] == 'id'

    # substituted component on list
    assert 'Simple' in schema['components']['schemas']
    assert 'PaginatedSimpleList' in schema['components']['schemas']
    substitution = schema['components']['schemas']['PaginatedSimpleList']
    assert substitution['type'] == 'object'
    assert substitution['properties']['results']['items']['$ref'] == '#/components/schemas/Simple'


def test_pagination_reusage(no_warnings):

    class XViewset(viewsets.ReadOnlyModelViewSet):
        queryset = SimpleModel.objects.all()
        serializer_class = SimpleSerializer
        pagination_class = pagination.LimitOffsetPagination

        @extend_schema(responses={'200': SimpleSerializer(many=True)})
        @action(methods=['GET'], detail=False)
        def custom_action(self):
            pass  # pragma: no cover

    class YViewset(XViewset):
        serializer_class = SimpleSerializer

    router = routers.SimpleRouter()
    router.register('x', XViewset, basename='x')
    router.register('y', YViewset, basename='y')
    generate_schema(None, patterns=router.urls)


def test_pagination_disabled_on_action(no_warnings):
    class XViewset(viewsets.ReadOnlyModelViewSet):
        queryset = SimpleModel.objects.all()
        serializer_class = SimpleSerializer
        pagination_class = pagination.LimitOffsetPagination

        @extend_schema(responses={'200': SimpleSerializer(many=True)})
        @action(methods=['GET'], detail=False, pagination_class=None)
        def custom_action(self):
            pass  # pragma: no cover

    class YViewset(XViewset):
        serializer_class = SimpleSerializer

    schema = generate_schema('x', YViewset)
    assert 'PaginatedSimpleList' in get_response_schema(schema['paths']['/x/']['get'])['$ref']
    assert 'Simple' in get_response_schema(
        schema['paths']['/x/custom_action/']['get']
    )['items']['$ref']


@mock.patch(
    'drf_spectacular.settings.spectacular_settings.SECURITY',
    [{'apiKeyAuth': []}]
)
@mock.patch(
    'drf_spectacular.settings.spectacular_settings.APPEND_COMPONENTS',
    {"securitySchemes": {"apiKeyAuth": {"type": "apiKey", "in": "header", "name": "Authorization"}}}
)
def test_manual_security_method_addition(no_warnings):
    @extend_schema(responses=OpenApiTypes.FLOAT)
    @api_view(['GET'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('/x/', view_function=view_func)
    operation_security = schema['paths']['/x/']['get']['security']
    schema_security = schema['components']['securitySchemes']
    assert len(operation_security) == 4 and any(['apiKeyAuth' in os for os in operation_security])
    assert len(schema_security) == 3 and 'apiKeyAuth' in schema_security


def test_basic_viewset_without_queryset_with_explicit_pk_typing(no_warnings):
    class XSerializer(serializers.Serializer):
        field = serializers.IntegerField()

    class XViewset(viewsets.ViewSet):
        serializer_class = XSerializer

        def retrieve(self, request, *args, **kwargs):
            pass  # pragma: no cover

    urlpatterns = [
        path("api/<path:some_var>/<uuid:pk>/", XViewset.as_view({"get": "retrieve"}))
    ]
    schema = generate_schema(None, patterns=urlpatterns)
    operation = schema['paths']['/api/{some_var}/{id}/']['get']
    assert operation['parameters'][0]['name'] == 'id'
    assert operation['parameters'][0]['schema']['format'] == 'uuid'


def test_multiple_media_types(no_warnings):
    @extend_schema(responses={
        (200, 'application/json'): OpenApiTypes.OBJECT,
        (200, 'application/pdf'): OpenApiTypes.BINARY,
    })
    class XAPIView(APIView):
        def get(self, request):
            pass  # pragma: no cover

    schema = generate_schema('x', view=XAPIView)
    content = schema['paths']['/x']['get']['responses']['200']['content']
    assert content['application/pdf']['schema']['format'] == 'binary'
    assert content['application/json']['schema']['type'] == 'object'


def test_token_auth_with_bearer_keyword(no_warnings):
    class CustomTokenAuthentication(TokenAuthentication):
        keyword = 'Bearer'

    @extend_schema(responses=OpenApiTypes.FLOAT)
    @api_view(['GET'])
    def view_func(request, format=None):
        pass  # pragma: no cover
    view_func.cls.authentication_classes = [CustomTokenAuthentication]

    schema = generate_schema('x', view_function=view_func)
    assert schema['components']['securitySchemes']['tokenAuth']['scheme'] == 'bearer'


@pytest.mark.parametrize('responses', [
    str,
    OpenApiTypes.STR,
    {'200': str},
    {'200': OpenApiTypes.STR},
])
def test_string_response_variations(no_warnings, responses):
    @extend_schema(responses=responses)
    @api_view(['GET'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('x', view_function=view_func)
    assert get_response_schema(schema['paths']['/x']['get'])['type'] == 'string'


def test_exclude_discovered_parameter(no_warnings):
    @extend_schema_view(list=extend_schema(parameters=[
        # keep 'offset', remove 'limit', and add 'random'
        OpenApiParameter('limit', exclude=True),
        OpenApiParameter('random', bool),
    ]))
    class XViewset(viewsets.ReadOnlyModelViewSet):
        queryset = SimpleModel.objects.all()
        serializer_class = SimpleSerializer
        pagination_class = pagination.LimitOffsetPagination

    schema = generate_schema('x', XViewset)
    parameters = schema['paths']['/x/']['get']['parameters']
    assert len(parameters) == 2
    assert parameters[0]['name'] == 'offset'
    assert parameters[1]['name'] == 'random'


def test_exclude_parameter_from_customized_autoschema(no_warnings):
    class CustomSchema(AutoSchema):
        def get_override_parameters(self):
            return [OpenApiParameter('test')]

    @extend_schema_view(list=extend_schema(parameters=[
        OpenApiParameter('test', exclude=True),  # exclude from class override
        OpenApiParameter('never_existed', exclude=True),  # provoke error
        OpenApiParameter('keep', bool),  # for sanity check
    ]))
    class XViewset(viewsets.ReadOnlyModelViewSet):
        queryset = SimpleModel.objects.all()
        serializer_class = SimpleSerializer
        schema = CustomSchema()

    schema = generate_schema('x', XViewset)
    parameters = schema['paths']['/x/']['get']['parameters']
    assert len(parameters) == 1
    assert parameters[0]['name'] == 'keep'


def test_manual_decimal_validator():
    # manually test this validator as it is not part of the default workflow
    class XSerializer(serializers.Serializer):
        field = serializers.FloatField(
            validators=[validators.DecimalValidator(max_digits=4, decimal_places=2)]
        )

    @extend_schema(request=XSerializer, responses=XSerializer)
    @api_view(['POST'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('x', view_function=view_func)
    field = schema['components']['schemas']['X']['properties']['field']
    assert field['maximum'] == 100
    assert field['minimum'] == -100


def test_serialization_with_decimal_values(no_warnings):
    class XSerializer(serializers.Serializer):
        field = serializers.DecimalField(
            decimal_places=2,
            min_value=Decimal('1'),
            max_value=Decimal('100.00'),
            max_digits=5,
            coerce_to_string=False,
        )
        field_coerced = serializers.DecimalField(
            decimal_places=2,
            min_value=Decimal('1'),
            max_value=Decimal('100.00'),
            max_digits=5,
            coerce_to_string=True,
        )

    @extend_schema(responses=XSerializer)
    @api_view(['GET'])
    def view_func(request):
        pass  # pragma: no cover

    schema = generate_schema('/x/', view_function=view_func)
    assert schema['components']['schemas']['X']['properties']['field'] == {
        'type': 'number',
        'format': 'double',
        'maximum': Decimal('100.00'),
        'minimum': Decimal('1'),
    }
    assert schema['components']['schemas']['X']['properties']['field_coerced'] == {
        'type': 'string',
        'format': 'decimal',
        'pattern': r'^\d{0,3}(?:\.\d{0,2})?$',
    }

    schema_yml = OpenApiYamlRenderer().render(schema, renderer_context={})
    assert b'maximum: 100.00\n' in schema_yml
    assert b'minimum: 1\n' in schema_yml


def test_non_supported_http_verbs(no_warnings):
    HTTP_METHODS = [
        'GET',
        'HEAD',
        'POST',
        'PUT',
        'DELETE',
        'CONNECT',
        'OPTIONS',
        'TRACE',
        'PATCH'
    ]
    for x in HTTP_METHODS:
        @extend_schema(request=int, responses=int)
        @api_view([x])
        def view_func(request, format=None):
            pass  # pragma: no cover

        generate_schema('x', view_function=view_func)


def test_nested_ro_serializer_has_required_fields_on_patch(no_warnings):
    # issue #249 raised a disparity problem between serializer name
    # generation and the actual serializer construction on PATCH.
    class XSerializer(serializers.Serializer):
        field = serializers.CharField()

    class YSerializer(serializers.Serializer):
        x_field = XSerializer(read_only=True)

    class YViewSet(viewsets.GenericViewSet):
        serializer_class = YSerializer
        queryset = SimpleModel.objects.all()

        def partial_update(self, request, *args, **kwargs):
            pass  # pragma: no cover

    schema = generate_schema('x', YViewSet)
    assert len(schema['components']['schemas']) == 3
    assert 'Y' in schema['components']['schemas']
    assert 'PatchedY' in schema['components']['schemas']
    assert 'required' in schema['components']['schemas']['X']


class M3(models.Model):
    """ test_path_param_from_related_model_pk_without_primary_key_true """
    related_field = models.ForeignKey(SimpleModel, on_delete=models.PROTECT, editable=False)
    many_related = models.ManyToManyField(SimpleModel, related_name='+')


@pytest.mark.parametrize('path', [
    r'x/(?P<related_field>[0-9a-f-]{36})',
    r'x/<related_field>',
])
def test_path_param_from_related_model_pk_without_primary_key_true(no_warnings, path):
    class M3Serializer(serializers.ModelSerializer):
        class Meta:
            fields = '__all__'
            model = M3

    class XViewset(viewsets.ModelViewSet):
        serializer_class = M3Serializer
        queryset = M3.objects.none()

    router = routers.SimpleRouter()
    router.register(path, XViewset)

    schema = generate_schema(None, patterns=router.urls)
    assert '/x/{related_field}/' in schema['paths']
    assert '/x/{related_field}/{id}/' in schema['paths']


def test_path_parameter_with_relationships(no_warnings):
    class PathParamParent(models.Model):
        pass

    class PathParamChild(models.Model):
        parent = models.ForeignKey(PathParamParent, on_delete=models.CASCADE)

    class PathParamGrandChild(models.Model):
        parent = models.ForeignKey(PathParamChild, on_delete=models.CASCADE)

    class PathParamChildSerializer(serializers.ModelSerializer):
        class Meta:
            fields = '__all__'
            model = PathParamChild

    class XViewset1(viewsets.ModelViewSet):
        serializer_class = PathParamChildSerializer
        queryset = PathParamChild.objects.none()
        lookup_field = 'id'

    class XViewset2(viewsets.ModelViewSet):
        serializer_class = PathParamChildSerializer
        queryset = PathParamChild.objects.none()
        lookup_field = 'parent'

    class XViewset3(viewsets.ModelViewSet):
        serializer_class = PathParamChildSerializer
        queryset = PathParamChild.objects.none()
        lookup_field = 'parent__id'  # Functionally the same as above

    class PathParamGrandChildSerializer(serializers.ModelSerializer):
        class Meta:
            fields = '__all__'
            model = PathParamGrandChild

    class XViewset4(viewsets.ModelViewSet):
        serializer_class = PathParamGrandChildSerializer
        queryset = PathParamGrandChild.objects.none()
        lookup_field = 'parent__parent'

    class XViewset5(viewsets.ModelViewSet):
        serializer_class = PathParamGrandChildSerializer
        queryset = PathParamGrandChild.objects.none()
        lookup_field = 'parent__parent__id'

    router = routers.SimpleRouter()
    router.register('child_by_id', XViewset1)
    router.register('child_by_parent_id', XViewset2)
    router.register('child_by_parent_id_alt', XViewset3)
    router.register('grand_child_by_grand_parent_id', XViewset4)
    router.register('grand_child_by_grand_parent_id_alt', XViewset5)

    schema = generate_schema(None, patterns=router.urls)

    # Basic cases:
    assert schema['paths']['/child_by_id/{id}/']['get']['parameters'][0] == {
        'description': 'A unique integer value identifying this path param child.',
        'in': 'path',
        'name': 'id',
        'schema': {'type': 'integer'},
        'required': True
    }
    assert schema['paths']['/child_by_parent_id/{parent}/']['get']['parameters'][0] == {
        'in': 'path',
        'name': 'parent',
        'schema': {'type': 'integer'},
        'required': True
    }

    # Can we traverse relationships?
    assert schema['paths']['/grand_child_by_grand_parent_id/{parent__parent}/']['get']['parameters'][0] == {
        'in': 'path',
        'name': 'parent__parent',
        'schema': {'type': 'integer'},
        'required': True
    }

    # Explicit `__id` handling:
    assert schema['paths']['/grand_child_by_grand_parent_id_alt/{parent__parent__id}/']['get']['parameters'][0] == {
        'description': 'A unique integer value identifying this path param grand child.',
        'in': 'path',
        'name': 'parent__parent__id',
        'schema': {'type': 'integer'},
        'required': True
    }
    assert schema['paths']['/child_by_parent_id_alt/{parent__id}/']['get']['parameters'][0] == {
        'description': 'A unique integer value identifying this path param child.',
        'in': 'path',
        'name': 'parent__id',
        'schema': {'type': 'integer'},
        'required': True
    }


def test_path_parameter_with_lookup_field(no_warnings):
    class JournalEntry(models.Model):
        recorded_at = models.DateTimeField()

    class JournalEntrySerializer(serializers.ModelSerializer):
        class Meta:
            fields = '__all__'
            model = JournalEntry

    class JournalEntryViewset(viewsets.ModelViewSet):
        serializer_class = JournalEntrySerializer
        queryset = JournalEntry.objects.none()
        lookup_field = 'recorded_at__date'

    class JournalEntryAltViewset(viewsets.ModelViewSet):
        serializer_class = JournalEntrySerializer
        queryset = JournalEntry.objects.none()
        lookup_field = 'recorded_at__date'
        lookup_url_kwarg = 'on'

    router = routers.SimpleRouter()
    router.register('journal', JournalEntryViewset)
    router.register('journal_alt', JournalEntryAltViewset)

    schema = generate_schema(None, patterns=router.urls)

    # TODO this is not 100% correct since "__date" transforms datetime to date,
    #  but most SQL modifiers don't change the type and we will tolerate that
    #  slight problem for now.
    assert schema['paths']['/journal/{recorded_at__date}/']['get']['parameters'][0] == {
        'in': 'path',
        'name': 'recorded_at__date',
        'required': True,
        'schema': {'format': 'date-time', 'type': 'string'},
    }
    assert schema['paths']['/journal_alt/{on}/']['get']['parameters'][0] == {
        'in': 'path',
        'name': 'on',
        'required': True,
        'schema': {'format': 'date-time', 'type': 'string'},
    }


@pytest.mark.contrib('psycopg2')
def test_multiple_choice_enum(no_warnings):
    from django.contrib.postgres.fields import ArrayField

    class M4(models.Model):
        multi = ArrayField(
            models.CharField(max_length=10, choices=(('A', 'A'), ('B', 'B'))),
            size=8,
        )

    class M4Serializer(serializers.ModelSerializer):
        class Meta:
            fields = '__all__'
            model = M4

    class XViewset(viewsets.ModelViewSet):
        serializer_class = M4Serializer
        queryset = M4.objects.none()

    schema = generate_schema('x', XViewset)
    assert 'MultiEnum' in schema['components']['schemas']
    prop = schema['components']['schemas']['M4']['properties']['multi']
    assert prop['type'] == 'array'
    assert prop['items']['$ref'] == '#/components/schemas/MultiEnum'


def test_explode_style_parameter_with_custom_schema(no_warnings):
    @extend_schema(
        parameters=[OpenApiParameter(
            name='bbox',
            type={'type': 'array', 'minItems': 4, 'maxItems': 6, 'items': {'type': 'number'}},
            location=OpenApiParameter.QUERY,
            required=False,
            style='form',
            explode=False,
        )],
        responses=OpenApiTypes.OBJECT,
    )
    @api_view(['GET'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('/x/', view_function=view_func)
    parameter = schema['paths']['/x/']['get']['parameters'][0]
    assert 'explode' in parameter
    assert 'style' in parameter
    assert parameter['schema']['type'] == 'array'


def test_incorrect_foreignkey_type_on_readonly_field(no_warnings):
    class ReferencingModel(models.Model):
        id = models.UUIDField(primary_key=True)
        referenced_model = models.ForeignKey(SimpleModel, on_delete=models.CASCADE)
        referenced_model_ro = models.ForeignKey(SimpleModel, on_delete=models.CASCADE)
        referenced_model_m2m = models.ManyToManyField(SimpleModel)
        referenced_model_m2m_ro = models.ManyToManyField(SimpleModel)

    class ReferencingModelSerializer(serializers.ModelSerializer):
        indirect_referenced_model_ro = serializers.PrimaryKeyRelatedField(
            source='referenced_model',
            read_only=True,
        )

        class Meta:
            fields = '__all__'
            read_only_fields = ['id', 'referenced_model_ro', 'referenced_model_m2m_ro']
            model = ReferencingModel

    class ReferencingModelViewset(viewsets.ModelViewSet):
        serializer_class = ReferencingModelSerializer
        queryset = ReferencingModel.objects.all()

    schema = generate_schema('/x/', ReferencingModelViewset)
    properties = schema['components']['schemas']['ReferencingModel']['properties']

    assert properties['referenced_model']['type'] == 'integer'
    assert properties['referenced_model_ro']['type'] == 'integer'
    assert properties['referenced_model_m2m']['items']['type'] == 'integer'
    assert properties['referenced_model_m2m_ro']['items']['type'] == 'integer'
    assert properties['indirect_referenced_model_ro']['type'] == 'integer'


@pytest.mark.parametrize(['sorting', 'result'], [
    (True, ['a', 'b', 'c']),
    (False, ['b', 'c', 'a']),
    (lambda x: (x['in'], x['name']), ['b', 'a', 'c']),
])
def test_parameter_sorting_setting(no_warnings, sorting, result):
    @extend_schema(
        parameters=[OpenApiParameter('b', str, 'header'), OpenApiParameter('c'), OpenApiParameter('a')],
        responses=OpenApiTypes.FLOAT
    )
    @api_view(['GET'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    with mock.patch(
        'drf_spectacular.settings.spectacular_settings.SORT_OPERATION_PARAMETERS', sorting
    ):
        schema = generate_schema('/x/', view_function=view_func)
        parameters = schema['paths']['/x/']['get']['parameters']
        assert [p['name'] for p in parameters] == result


@pytest.mark.parametrize(['sorting', 'result'], [
    (True, ['/a/', '/b/', '/c/']),
    (False, ['/c/', '/a/', '/b/']),
    (lambda x: {'/c/': 1, '/b/': 2, '/a/': 3}.get(x[0]), ['/c/', '/b/', '/a/']),
])
def test_operation_sorting_setting(no_warnings, sorting, result):
    @extend_schema(responses=OpenApiTypes.ANY)
    @api_view(['GET'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    urlpatterns = [
        path('/c/', view_func),
        path('/a/', view_func),
        path('/b/', view_func),
    ]
    with mock.patch(
        'drf_spectacular.settings.spectacular_settings.SORT_OPERATIONS', sorting
    ):
        schema = generate_schema(None, patterns=urlpatterns)
        assert list(schema['paths'].keys()) == result


def test_response_headers_without_response_body(no_warnings):
    @extend_schema(
        responses={301: None},
        tags=["Registration"],
        parameters=[
            OpenApiParameter(
                name="Location",
                type=OpenApiTypes.URI,
                location=OpenApiParameter.HEADER,
                description="/",
                response=[301]
            )
        ]
    )
    @api_view(['GET'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('/x/', view_function=view_func)
    assert 'Location' in schema['paths']['/x/']['get']['responses']['301']['headers']
    assert 'content' not in schema['paths']['/x/']['get']['responses']['301']


def test_customized_parsers_and_renderers_on_viewset(no_warnings):
    class XViewset(viewsets.ModelViewSet):
        serializer_class = SimpleSerializer
        queryset = SimpleModel.objects.none()
        parser_classes = [parsers.MultiPartParser]

        def get_renderers(self):
            if self.action == 'json_in_multi_out':
                return [renderers.MultiPartRenderer()]
            else:
                return [renderers.HTMLFormRenderer()]

        @action(methods=['POST'], detail=False, parser_classes=[parsers.JSONParser])
        def json_in_multi_out(self, request):
            pass  # pragma: no cover

    schema = generate_schema('x', XViewset)

    create_op = schema['paths']['/x/']['post']
    assert len(create_op['requestBody']['content']) == 1
    assert 'multipart/form-data' in create_op['requestBody']['content']
    assert len(create_op['responses']['201']['content']) == 1
    assert 'text/html' in create_op['responses']['201']['content']

    action_op = schema['paths']['/x/json_in_multi_out/']['post']
    assert len(action_op['requestBody']['content']) == 1
    assert 'application/json' in action_op['requestBody']['content']
    assert len(action_op['responses']['200']['content']) == 1
    assert 'multipart/form-data' in action_op['responses']['200']['content']


def test_technically_unnecessary_serializer_patch(no_warnings):
    # ideally this extend_schema would not be necessary
    @extend_schema_view(delete=extend_schema(responses=None))
    class XAPIView(generics.DestroyAPIView):
        queryset = SimpleModel.objects.none()

    schema = generate_schema('/x/', view=XAPIView)
    assert 'No response' in schema['paths']['/x/']['delete']['responses']['204']['description']


def test_any_placeholder_on_request_response(no_warnings):
    @extend_schema_field(OpenApiTypes.ANY)
    class CustomField(serializers.IntegerField):
        pass  # pragma: no cover

    class XSerializer(serializers.Serializer):
        method_field = serializers.SerializerMethodField(help_text='Any')
        custom_field = CustomField()

        def get_method_field(self, obj) -> typing.Any:
            return  # pragma: no cover

    @extend_schema(request=typing.Any, responses=XSerializer)
    @api_view(['POST'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('/x/', view_function=view_func)
    assert get_request_schema(schema['paths']['/x/']['post']) == {}

    properties = schema['components']['schemas']['X']['properties']
    assert properties['custom_field'] == {}
    assert properties['method_field'] == {'readOnly': True, 'description': 'Any'}


def test_categorized_choices(no_warnings, clear_caches):
    media_choices = [
        ('Audio', (('vinyl', 'Vinyl'), ('cd', 'CD'))),
        ('Video', (('vhs', 'VHS Tape'), ('dvd', 'DVD'))),
        ('unknown', 'Unknown'),
    ]
    media_choices_audio = [
        ('Audio', (('vinyl', 'Vinyl'), ('cd', 'CD'))),
        ('unknown', 'Unknown'),
    ]

    class M9(models.Model):
        cat_choice = models.CharField(max_length=10, choices=media_choices)

    class M9Serializer(serializers.ModelSerializer):
        audio_choice = serializers.ChoiceField(choices=media_choices_audio)

        class Meta:
            fields = '__all__'
            model = M9

    class XViewset(viewsets.ModelViewSet):
        serializer_class = M9Serializer
        queryset = M9.objects.none()

    with mock.patch(
        'drf_spectacular.settings.spectacular_settings.ENUM_NAME_OVERRIDES',
        {'MediaEnum': media_choices}
    ):
        schema = generate_schema('x', XViewset)

    # test base functionality of flattening categories
    assert schema['components']['schemas']['AudioChoiceEnum']['enum'] == [
        'vinyl', 'cd', 'unknown'
    ]
    # test override match works synchronously
    assert schema['components']['schemas']['MediaEnum']['enum'] == [
        'vinyl', 'cd', 'vhs', 'dvd', 'unknown'
    ]


@mock.patch('drf_spectacular.settings.spectacular_settings.SCHEMA_PATH_PREFIX', '/api/v[0-9]/')
@mock.patch('drf_spectacular.settings.spectacular_settings.SCHEMA_PATH_PREFIX_TRIM', True)
def test_schema_path_prefix_trim(no_warnings):
    @extend_schema(request=typing.Any, responses=typing.Any)
    @api_view(['POST'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('/api/v1/x/', view_function=view_func)
    assert '/x/' in schema['paths']


def test_nameless_root_endpoint(no_warnings):
    @extend_schema(request=typing.Any, responses=typing.Any)
    @api_view(['POST'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('/', view_function=view_func)
    assert schema['paths']['/']['post']['operationId'] == 'root_create'


def test_list_and_pagination_on_non_2XX_schemas(no_warnings):
    @extend_schema_view(
        list=extend_schema(responses={
            200: SimpleSerializer,
            400: {'type': 'object', 'properties': {'code': {'type': 'string'}}},
            403: OpenApiTypes.OBJECT
        })
    )
    class XViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
        serializer_class = SimpleSerializer
        queryset = SimpleModel.objects.none()
        pagination_class = pagination.LimitOffsetPagination

    schema = generate_schema('x', XViewset)
    assert get_response_schema(schema['paths']['/x/']['get']) == {
        '$ref': '#/components/schemas/PaginatedSimpleList'
    }
    assert get_response_schema(schema['paths']['/x/']['get'], '400') == {
        'type': 'object', 'properties': {'code': {'type': 'string'}}
    }
    assert get_response_schema(schema['paths']['/x/']['get'], '403') == {
        'type': 'object', 'additionalProperties': {}
    }


def test_openapi_response_wrapper(no_warnings):
    @extend_schema_view(
        create=extend_schema(description='creation description', responses={
            201: OpenApiResponse(response=int, description='creation with int response.'),
            222: OpenApiResponse(description='creation with no response.'),
            223: None,
            224: int,
        }),
        list=extend_schema(responses=OpenApiResponse(
            response=OpenApiTypes.INT,
            description='a list that actually returns numbers',
            examples=[OpenApiExample('One', 1), OpenApiExample('Two', 2)],
        )),
    )
    class XViewset(viewsets.ModelViewSet):
        serializer_class = SimpleSerializer
        queryset = SimpleModel.objects.none()

    schema = generate_schema('/x', XViewset)
    assert schema['paths']['/x/']['get']['responses'] == {
        '200': {
            'content': {
                'application/json': {
                    'schema': {'type': 'integer'},
                    'examples': {'One': {'value': 1}, 'Two': {'value': 2}}
                }
            },
            'description': 'a list that actually returns numbers'
        }
    }
    assert schema['paths']['/x/']['post']['description'] == 'creation description'
    assert schema['paths']['/x/']['post']['responses'] == {
        '201': {
            'content': {'application/json': {'schema': {'type': 'integer'}}},
            'description': 'creation with int response.'
        },
        '222': {'description': 'creation with no response.'},
        '223': {'description': 'No response body'},
        '224': {'content': {'application/json': {'schema': {'type': 'integer'}}}, 'description': ''}
    }


def test_prefix_estimation_with_re_special_chars_as_literals_in_path(no_warnings):
    # make sure prefix estimation logic does not choke on reserved RE chars
    @extend_schema(request=typing.Any, responses=typing.Any)
    @api_view(['POST'])
    def view_func1(request, format=None):
        pass  # pragma: no cover

    @extend_schema(request=typing.Any, responses=typing.Any)
    @api_view(['POST'])
    def view_func2(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema(None, patterns=[
        path('/\\/x/', view_func1),
        path('/\\/y/', view_func2)
    ])
    assert schema['paths']['/\\/x/']['post']['tags'] == ['x']


def test_nested_router_urls(no_warnings):
    # somewhat tailored to drf-nested-routers but also serves a generic purpose
    # as "id" coercion also makes sense for "_pk" suffixes.
    class RouteNestedMaildropModel(models.Model):
        renamed_id = models.IntegerField(primary_key=True)

    class RouteNestedClientModel(models.Model):
        id = models.UUIDField(primary_key=True)

    class RouteNestedModel(models.Model):
        client = models.ForeignKey(RouteNestedClientModel, on_delete=models.CASCADE)
        maildrop = models.ForeignKey(RouteNestedMaildropModel, on_delete=models.CASCADE)

    class RouteNestedViewset(viewsets.ModelViewSet):
        queryset = RouteNestedModel.objects.all()
        serializer_class = SimpleSerializer

    urlpatterns = [
        path(
            '/clients/{client_pk}/maildrops/{maildrop_pk}/recipients/{pk}/',
            RouteNestedViewset.as_view({'get': 'retrieve'})
        ),
    ]
    schema = generate_schema(None, patterns=urlpatterns)
    operation = schema['paths']['/clients/{client_pk}/maildrops/{maildrop_pk}/recipients/{id}/']['get']
    assert operation['parameters'][0]['name'] == 'client_pk'
    assert operation['parameters'][0]['schema'] == {'format': 'uuid', 'type': 'string'}
    assert operation['parameters'][2]['name'] == 'maildrop_pk'
    assert operation['parameters'][2]['schema'] == {'type': 'integer'}


@pytest.mark.parametrize('value', [
    datetime.datetime(year=2021, month=1, day=1),
    datetime.date(year=2021, month=1, day=1),
    datetime.time(),
    datetime.timedelta(days=1),
    uuid.uuid4(),
    Decimal(),
    b'deadbeef'
])
def test_yaml_encoder_parity(no_warnings, value):
    # make sure our YAML renderer does not choke on objects that are fine with
    # rest_framework.encoders.JSONEncoder
    assert OpenApiJsonRenderer().render(value)
    assert OpenApiYamlRenderer().render(value)


@pytest.mark.parametrize(['comp_schema', 'discarded'], [
    ({'type': 'object'}, True),
    ({'type': 'object', 'properties': {}}, True),
    ({'type': 'object', 'additionalProperties': {}}, False),
    ({'type': 'object', 'additionalProperties': {'type': 'number'}}, False),
    ({'type': 'number'}, False),
    ({'type': 'array', 'items': {'type': 'number'}}, False),
])
def test_serializer_extension_with_non_object_schema(no_warnings, comp_schema, discarded):
    class XSerializer(serializers.Serializer):
        field = serializers.CharField()

    class XExtension(OpenApiSerializerExtension):
        target_class = XSerializer

        def map_serializer(self, auto_schema, direction):
            return comp_schema

    class XAPIView(APIView):
        @extend_schema(request=XSerializer, responses=XSerializer)
        def post(self, request):
            pass  # pragma: no cover

    schema = generate_schema('x', view=XAPIView)

    operation = schema['paths']['/x']['post']
    if discarded:
        assert 'requestBody' not in operation
    else:
        assert get_request_schema(operation)['$ref'] == '#/components/schemas/X'
        assert schema['components']['schemas']['X'] == comp_schema


def test_response_header_with_serializer_component(no_warnings):
    class XSerializer(serializers.Serializer):
        field = serializers.CharField()

    @extend_schema(
        request=OpenApiTypes.ANY,
        responses=OpenApiTypes.ANY,
        parameters=[OpenApiParameter(
            name='test',
            type=XSerializer,
            location=OpenApiParameter.HEADER,
            response=True,
        )]
    )
    @api_view(['POST'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('x', view_function=view_func)
    assert 'X' in schema['components']['schemas']
    assert schema['paths']['/x']['post']['responses']['200']['headers'] == {
        'test': {'schema': {'$ref': '#/components/schemas/X'}}
    }


def test_extend_schema_noop_request_content_type(no_warnings):
    @extend_schema(
        request={
            'application/json': None,  # for completeness, not necessary
            'application/pdf': OpenApiTypes.BINARY
        },
        responses=OpenApiTypes.ANY,
    )
    @api_view(['POST'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('x', view_function=view_func)
    assert 'application/pdf' in schema['paths']['/x']['post']['requestBody']['content']
    assert 'application/json' not in schema['paths']['/x']['post']['requestBody']['content']


def test_viewset_reverse_list_detection_override(no_warnings):
    class XViewset(viewsets.ReadOnlyModelViewSet):
        queryset = SimpleModel.objects.all()
        serializer_class = SimpleSerializer

        @extend_schema(
            # without explicit operation_id, this operation is detected as non-list and thus
            # will be named "x_retrieve", which create a collision with the actual retrieve.
            operation_id='x_list',
            parameters=[OpenApiParameter("format")],
            responses={(200, "*/*"): OpenApiTypes.STR},
        )
        def list(self, request, *args, **kwargs):
            pass  # pragma: no cover

    schema = generate_schema('/x', XViewset)
    assert schema['paths']['/x/']['get']['parameters'][0]['name'] == 'format'
    assert schema['paths']['/x/']['get']['operationId'] == 'x_list'
    assert schema['paths']['/x/{id}/']['get']['operationId'] == 'x_retrieve'


def test_list_serializer_with_read_only_field_on_model_property(no_warnings):
    class M7Model(models.Model):
        @property
        def all_groups(self) -> typing.List[int]:
            return [1, 2, 3]  # pragma: no cover

    class XField(serializers.ReadOnlyField):
        pass

    class XSerializer(serializers.ModelSerializer):
        groups = serializers.ListSerializer(source="all_groups", child=XField(), read_only=True)

        class Meta:
            model = M7Model
            fields = '__all__'

    class XViewset(viewsets.ReadOnlyModelViewSet):
        queryset = M7Model.objects.none()
        serializer_class = XSerializer

    schema = generate_schema('x', XViewset)
    assert schema['components']['schemas']['X']['properties']['groups'] == {
        'type': 'array',
        'items': {'type': 'array', 'items': {'type': 'integer'}, 'readOnly': True},
        'readOnly': True
    }


def test_extend_schema_serializer_field_deprecation(no_warnings):
    @extend_schema_serializer(deprecate_fields=['old'])
    class XSerializer(serializers.Serializer):
        old = serializers.IntegerField()
        new = serializers.IntegerField()

    class XView(generics.ListCreateAPIView):
        serializer_class = XSerializer

    schema = generate_schema('/x', view=XView)
    assert schema['components']['schemas']['X']['properties']['new'] == {
        'type': 'integer',
    }
    assert schema['components']['schemas']['X']['properties']['old'] == {
        'type': 'integer', 'deprecated': True
    }


def test_paginated_list_serializer_with_dict_field(no_warnings):
    class XAPIView(generics.ListAPIView):
        pagination_class = pagination.LimitOffsetPagination

        @extend_schema(responses=serializers.ListSerializer(child=serializers.DictField()))
        def get(self, request):
            pass  # pragma: no cover

    schema = generate_schema('/x/', view=XAPIView)
    assert get_response_schema(schema['paths']['/x/']['get'])['properties']['results'] == {
        'type': 'array', 'items': {'type': 'object', 'additionalProperties': {}}
    }


def test_serializer_method_field_with_functools_partial(no_warnings):
    class XSerializer(serializers.Serializer):
        foo = serializers.SerializerMethodField()
        bar = serializers.SerializerMethodField()

        @extend_schema_field(OpenApiTypes.DATE)
        def _private_method_foo(self, field, extra_param):
            return 'foo'  # pragma: no cover

        def _private_method_bar(self, field, extra_param) -> int:
            return 1  # pragma: no cover

        get_foo = partialmethod(_private_method_foo, extra_param='foo')
        get_bar = partialmethod(_private_method_bar, extra_param='bar')

    @extend_schema(request=XSerializer, responses=XSerializer)
    @api_view(['POST'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('/x/', view_function=view_func)
    assert schema['components']['schemas']['X']['properties'] == {
        'foo': {'type': 'string', 'format': 'date', 'readOnly': True},
        'bar': {'type': 'integer', 'readOnly': True}
    }


@mock.patch(
    'drf_spectacular.settings.spectacular_settings.ENABLE_LIST_MECHANICS_ON_NON_2XX', True
)
def test_disable_list_mechanics_on_non_2XX(no_warnings):
    @extend_schema(
        request=SimpleSerializer,
        responses={
            200: SimpleSerializer(many=True),
            400: SimpleSerializer(many=True),
        }
    )
    @api_view(['POST'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('/x/', view_function=view_func)
    assert get_response_schema(schema['paths']['/x/']['post'], status='200') == {
        'type': 'array', 'items': {'$ref': '#/components/schemas/Simple'}
    }
    assert get_response_schema(schema['paths']['/x/']['post'], status='400') == {
        'type': 'array', 'items': {'$ref': '#/components/schemas/Simple'}
    }


@mock.patch(
    'drf_spectacular.settings.spectacular_settings.AUTHENTICATION_WHITELIST', [TokenAuthentication]
)
def test_authentication_whitelist(no_warnings):
    class XViewset(viewsets.ReadOnlyModelViewSet):
        serializer_class = SimpleSerializer
        queryset = SimpleModel.objects.none()
        authentication_classes = [BasicAuthentication, TokenAuthentication]

    schema = generate_schema('/x', XViewset)
    assert list(schema['components']['securitySchemes']) == ['tokenAuth']
    assert schema['paths']['/x/']['get']['security'] == [{'tokenAuth': []}, {}]


def test_request_response_raw_schema_annotation(no_warnings):
    @extend_schema(
        request={'application/pdf': {'type': 'string', 'format': 'binary'}},
        responses={(200, 'application/pdf'): {'type': 'string', 'format': 'binary'}}
    )
    @api_view(['POST'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('/x/', view_function=view_func)
    op = schema['paths']['/x/']['post']
    assert op['requestBody']['content']['application/pdf']['schema'] == {
        'type': 'string', 'format': 'binary'
    }
    assert op['responses']['200']['content']['application/pdf']['schema'] == {
        'type': 'string', 'format': 'binary'
    }


def test_serializer_modelfield_and_methodfield_with_default_value(no_warnings):
    class M8Model(models.Model):
        field = models.IntegerField()

    class XSerializer(serializers.ModelSerializer):
        field = serializers.ModelField(
            model_field=M8Model()._meta.get_field('field'),
            default=3
        )
        field_smf = serializers.SerializerMethodField(default=4)

        def get_field_smf(self, obj) -> int:
            return 0  # pragma: no cover

        class Meta:
            model = M8Model
            fields = '__all__'

    class XViewset(viewsets.ModelViewSet):
        serializer_class = XSerializer
        queryset = M8Model.objects.all()

    schema = generate_schema('x', XViewset)
    assert schema['components']['schemas']['X']['properties']['field'] == {
        'type': 'integer', 'default': 3
    }
    assert schema['components']['schemas']['X']['properties']['field_smf'] == {
        'type': 'integer', 'readOnly': True, 'default': 4
    }


def test_literal_dot_in_regex_path(no_warnings):
    @extend_schema(
        responses=OpenApiTypes.ANY,
        parameters=[
            OpenApiParameter('filename', str, OpenApiParameter.PATH),
            OpenApiParameter('ext', str, OpenApiParameter.PATH)
        ]
    )
    @api_view(['GET'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    urlpatterns = [
        re_path('^file/(?P<filename>.*)\\.(?P<ext>\\w+)$', view_func)
    ]
    schema = generate_schema(None, patterns=urlpatterns)
    assert '/file/{filename}.{ext}' in schema['paths']


def test_customized_lookup_url_kwarg(no_warnings):
    class XViewset(viewsets.ModelViewSet):
        serializer_class = SimpleSerializer
        queryset = SimpleModel.objects.all()
        lookup_url_kwarg = 'custom_name'

    schema = generate_schema('/x', XViewset)
    assert schema['paths']['/x/{custom_name}/']['get']['parameters'][0] == {
        'in': 'path',
        'name': 'custom_name',
        'schema': {'type': 'integer'},
        'description': 'A unique integer value identifying this simple model.',
        'required': True
    }


@pytest.mark.skipif(DJANGO_VERSION < '3', reason='Bug in Django\'s simplify_regex()')
def test_regex_path_parameter_discovery_pattern(no_warnings):
    @extend_schema(responses=OpenApiTypes.FLOAT)
    @api_view(['GET'])
    def pi(request, foo):
        pass  # pragma: no cover

    urlpatterns = [
        re_path(r'^/pi/(?P<precision>(\d+)-[\w|\.]+(failed|success))', pi)
    ]
    schema = generate_schema(None, patterns=urlpatterns)

    assert schema['paths']['/pi/{precision}']['get']['parameters'][0] == {
        'in': 'path',
        'name': 'precision',
        'schema': {'type': 'string', 'pattern': '(\\d+)-[\\w|\\.]+(failed|success)'},
        'required': True
    }


class PathParameterLookupModel(models.Model):
    """ test_path_parameter_priority_matching """
    field = models.IntegerField()


@pytest.mark.parametrize(['path_func', 'path_str', 'pattern', 'parameter_types'], [
    # django typed -> use
    (path, '/{id}/', '<int:pk>/', ['integer']),
    # untyped -> get from model
    (path, '/{id}/', '<pk>/', ['integer']),
    # non-default pattern -> use
    (re_path, '/{id}/', r'(?P<pk>[a-z]{2}(-[a-z]{2})?)/', ['string']),
    # default pattern -> get from model
    (re_path, '/{id}/', r'(?P<pk>[^/.]+)/$', ['integer']),
    # same mechanics for non-pk field discovery from model
    (re_path, '/{field}/t/{id}/', r'^(?P<field>[^/.]+)/t/(?P<pk>[a-z]+)/', ['integer', 'string']),
    (re_path, '/{field}/t/{id}/', r'^(?P<field>[A-Z\(\)]+)/t/(?P<pk>[^/.]+)/', ['string', 'integer']),
])
def test_path_parameter_priority_matching(no_warnings, path_func, path_str, pattern, parameter_types):
    class LookupSerializer(serializers.ModelSerializer):
        class Meta:
            model = PathParameterLookupModel
            fields = '__all__'

    class XAPIView(generics.RetrieveAPIView):
        serializer_class = LookupSerializer
        queryset = PathParameterLookupModel.objects.all()

    # make sure regex are valid
    if path_func == re_path:
        re.compile(pattern)

    urlpatterns = [path_func(pattern, XAPIView.as_view())]
    schema = generate_schema(None, patterns=urlpatterns)
    parameters = schema['paths'][path_str]['get']['parameters']

    assert len(parameters) == len(parameter_types)
    for parameter_type, parameter in zip(parameter_types, parameters):
        assert parameter['schema']['type'] == parameter_type
        assert parameter_type != 'string' or 'pattern' in parameter['schema']


@pytest.mark.parametrize('import_string', IMPORT_STRINGS)
def test_import_strings_in_default_settings(import_string):
    assert import_string in SPECTACULAR_DEFAULTS


@mock.patch(
    'drf_spectacular.settings.spectacular_settings.PATH_CONVERTER_OVERRIDES', {
        'int': str,  # override default behavior
        'signed_int': {'type': 'integer', 'format': 'signed'},
    }
)
def test_path_converter_override(no_warnings):
    @extend_schema(responses=OpenApiTypes.FLOAT)
    @api_view(['GET'])
    def pi(request, foo):
        pass  # pragma: no cover

    class SignedIntConverter(StringConverter):
        regex = r'\-[0-9]+'

    class HexConverter(StringConverter):
        regex = r'[a-f0-9]+'

    register_converter(SignedIntConverter, 'signed_int')
    register_converter(HexConverter, 'hex')

    urlpatterns = [
        path('/a/<int:var>/', pi),
        path('/b/<signed_int:var>/', pi),
        path('/c/<hex:var>/', pi),
    ]
    schema = generate_schema(None, patterns=urlpatterns)

    assert schema['paths']['/a/{var}/']['get']['parameters'][0]['schema'] == {
        'type': 'string',
    }
    assert schema['paths']['/b/{var}/']['get']['parameters'][0]['schema'] == {
        'type': 'integer', 'format': 'signed'
    }
    assert schema['paths']['/c/{var}/']['get']['parameters'][0]['schema'] == {
        'type': 'string', 'pattern': '[a-f0-9]+'
    }


@pytest.mark.parametrize('kwargs,expected', [
    (
        {'max_value': -2147483648},
        {'type': 'integer', 'maximum': -2147483648},
    ),
    (
        {'max_value': -2147483649},
        {'type': 'integer', 'maximum': -2147483649, 'format': 'int64'},
    ),
    (
        {'max_value': 2147483647},
        {'type': 'integer', 'maximum': 2147483647},
    ),
    (
        {'max_value': 2147483648},
        {'type': 'integer', 'maximum': 2147483648, 'format': 'int64'},
    ),
    (
        {'min_value': -2147483648},
        {'type': 'integer', 'minimum': -2147483648},
    ),
    (
        {'min_value': -2147483649},
        {'type': 'integer', 'minimum': -2147483649, 'format': 'int64'},
    ),
    (
        {'min_value': 2147483647},
        {'type': 'integer', 'minimum': 2147483647},
    ),
    (
        {'min_value': 2147483648},
        {'type': 'integer', 'minimum': 2147483648, 'format': 'int64'},
    ),
])
def test_int64_detection(kwargs, expected, no_warnings):
    class XSerializer(serializers.Serializer):
        field = serializers.IntegerField(**kwargs)

    @extend_schema(request=XSerializer, responses=XSerializer)
    @api_view(['GET'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('x', view_function=view_func)
    assert schema['components']['schemas']['X']['properties']['field'] == expected


def test_description_whitespace_stripping(no_warnings):
    class XViewset(viewsets.ModelViewSet):
        """ view: oneliner with leading/trailing whitespace """
        serializer_class = SimpleSerializer
        queryset = SimpleModel.objects.none()

        def retrieve(self, request):
            """  retrieve: oneliner with leading/trailing whitespace  """
            pass  # pragma: no cover

        def create(self, request):
            """
                create: multi line indented  
                description docstring        
            """  # noqa: W291
            pass  # pragma: no cover

    schema = generate_schema('/x', XViewset)
    assert schema['paths']['/x/']['get']['description'] == (
        'view: oneliner with leading/trailing whitespace'
    )
    assert schema['paths']['/x/{id}/']['get']['description'] == (
        'retrieve: oneliner with leading/trailing whitespace'
    )
    assert schema['paths']['/x/']['post']['description'] == (
        'create: multi line indented\ndescription docstring'
    )


@pytest.mark.parametrize('list_variation', [
    serializers.ListField, serializers.ListSerializer
])
def test_double_nested_list_serializer(no_warnings, list_variation):
    class XSerializer(serializers.Serializer):
        id = serializers.IntegerField()

    class XNestedListSerializer(serializers.Serializer):
        nested_xs = list_variation(child=XSerializer(many=True))

    class XAPIView(generics.GenericAPIView):
        @extend_schema(request=XNestedListSerializer, responses=XNestedListSerializer)
        def post(self, request, *args, **kwargs):
            pass  # pragma: no cover

    schema = generate_schema('x', view=XAPIView)
    operation = schema['paths']['/x']['post']
    assert get_request_schema(operation) == {'$ref': '#/components/schemas/XNestedList'}
    assert get_response_schema(operation) == {'$ref': '#/components/schemas/XNestedList'}
    assert schema['components']['schemas']['XNestedList']['properties']['nested_xs'] == {
        'type': 'array',
        'items': {'type': 'array', 'items': {'$ref': '#/components/schemas/X'}}
    }


@pytest.mark.parametrize('extend_method, api_view_method', [
    ('get', 'GET'),
    ('GET', 'get'),
])
def test_api_view_decorator_case_insensitive(no_warnings, extend_method, api_view_method):

    @extend_schema(methods=[extend_method], responses=OpenApiTypes.FLOAT)
    @api_view([api_view_method])
    def pi(request):
        pass  # pragma: no cover

    schema = generate_schema('x', view_function=pi)
    operation = schema['paths']['/x']['get']
    assert get_response_schema(operation) == {'type': 'number', 'format': 'float'}


@pytest.mark.parametrize('extend_method, action_method', [
    ('get', 'GET'),
    ('GET', 'get'),
])
def test_action_decorator_case_insensitive(no_warnings, extend_method, action_method):

    class XViewSet(viewsets.ReadOnlyModelViewSet):
        queryset = SimpleModel.objects.all()
        serializer_class = SimpleSerializer

        @extend_schema(methods=[extend_method], summary='A custom action!')
        @action(methods=[action_method], detail=True)
        def custom_action(self):
            pass  # pragma: no cover

    schema = generate_schema('x', viewset=XViewSet)
    assert schema['paths']['/x/{id}/custom_action/']['get']['summary'] == 'A custom action!'


def test_extend_schema_view_isolation(no_warnings):
    class AnimalViewSet(viewsets.GenericViewSet):
        serializer_class = SimpleSerializer
        queryset = SimpleModel.objects.all()

        @action(detail=False)
        def notes(self, request):
            pass  # pragma: no cover

    @extend_schema_view(notes=extend_schema(summary='List mammals.'))
    class MammalViewSet(AnimalViewSet):
        pass

    @extend_schema_view(notes=extend_schema(summary='List insects.'))
    class InsectViewSet(AnimalViewSet):
        pass

    router = routers.SimpleRouter()
    router.register('api/mammals', MammalViewSet)
    router.register('api/insects', InsectViewSet)

    schema = generate_schema(None, patterns=router.urls)
    assert schema['paths']['/api/mammals/notes/']['get']['summary'] == 'List mammals.'
    assert schema['paths']['/api/insects/notes/']['get']['summary'] == 'List insects.'


def test_extend_schema_view_layering(no_warnings):
    class YSerializer(serializers.Serializer):
        field = serializers.FloatField()

    class ZSerializer(serializers.Serializer):
        field = serializers.UUIDField()

    class XViewSet(viewsets.ReadOnlyModelViewSet):
        queryset = SimpleModel.objects.all()
        serializer_class = SimpleSerializer

    @extend_schema_view(retrieve=extend_schema(responses=YSerializer))
    class YViewSet(XViewSet):
        pass

    @extend_schema_view(retrieve=extend_schema(responses=ZSerializer))
    class ZViewSet(YViewSet):
        pass

    router = routers.SimpleRouter()
    router.register('x', XViewSet)
    router.register('y', YViewSet)
    router.register('z', ZViewSet)
    schema = generate_schema(None, patterns=router.urls)
    resp = {
        c: get_response_schema(schema['paths'][f'/{c.lower()}/{{id}}/']['get'])
        for c in ['X', 'Y', 'Z']
    }
    assert resp['X'] == {'$ref': '#/components/schemas/Simple'}
    assert resp['Y'] == {'$ref': '#/components/schemas/Y'}
    assert resp['Z'] == {'$ref': '#/components/schemas/Z'}


def test_extend_schema_view_extend_schema_crosstalk(no_warnings):
    class XSerializer(serializers.Serializer):
        field = serializers.FloatField()

    # extend_schema_view provokes decorator reordering in extend_schema
    @extend_schema(tags=['X'])
    @extend_schema_view(retrieve=extend_schema(responses=XSerializer))
    class XViewSet(viewsets.ReadOnlyModelViewSet):
        queryset = SimpleModel.objects.all()
        serializer_class = SimpleSerializer

    @extend_schema(tags=['Y'])
    class YViewSet(XViewSet):
        pass

    router = routers.SimpleRouter()
    router.register('x', XViewSet)
    router.register('y', YViewSet)
    schema = generate_schema(None, patterns=router.urls)
    op = {
        c: schema['paths'][f'/{c.lower()}/{{id}}/']['get'] for c in ['X', 'Y']
    }
    assert op['X']['tags'] == ['X']
    assert op['Y']['tags'] == ['Y']


def test_extend_schema_view_on_api_view(no_warnings):
    @extend_schema_view(
        get=extend_schema(description='get desc', responses=OpenApiTypes.FLOAT),
        post=extend_schema(description='post desc', request=OpenApiTypes.INT, responses=OpenApiTypes.UUID),
    )
    @api_view(['GET', 'POST'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('/x/', view_function=view_func)
    op_get = schema['paths']['/x/']['get']
    op_post = schema['paths']['/x/']['post']
    assert get_response_schema(op_get) == {'type': 'number', 'format': 'float'}
    assert get_response_schema(op_post) == {'format': 'uuid', 'type': 'string'}
    assert get_request_schema(op_post) == {'type': 'integer'}


@mock.patch('drf_spectacular.settings.spectacular_settings.COMPONENT_SPLIT_REQUEST', True)
@pytest.mark.parametrize('ro,wo', [(True, False), (False, True), (False, False)])
def test_nested_empty_direction_serializer_with_split(no_warnings, ro, wo):
    class NestedSerializer(serializers.Serializer):
        field = serializers.IntegerField(write_only=wo, read_only=ro)

    class XSerializer(serializers.Serializer):
        field = NestedSerializer(many=True)

    @extend_schema(request=XSerializer, responses=XSerializer)
    @api_view(['POST'])
    def pi(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('/x', view_function=pi)
    operation = schema['paths']['/x']['post']
    if wo:
        assert get_request_schema(operation) == {'$ref': '#/components/schemas/XRequest'}
        assert operation['responses']['200'] == {'description': 'No response body'}
    elif ro:
        assert 'requestBody' not in operation
        assert get_response_schema(operation) == {'$ref': '#/components/schemas/X'}
    else:
        assert get_request_schema(operation) == {'$ref': '#/components/schemas/XRequest'}
        assert get_response_schema(operation) == {'$ref': '#/components/schemas/X'}


@mock.patch('drf_spectacular.settings.spectacular_settings.COMPONENT_SPLIT_REQUEST', True)
@pytest.mark.parametrize('ro,wo', [(True, False), (False, True), (False, False)])
def test_empty_direction_list_serializer_with_split(no_warnings, ro, wo):
    class XSerializer(serializers.Serializer):
        field = serializers.IntegerField(write_only=wo, read_only=ro)

    @extend_schema(request=XSerializer(many=True), responses=XSerializer(many=True))
    @api_view(['POST'])
    def pi(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('/x', view_function=pi)
    operation = schema['paths']['/x']['post']
    if wo:
        assert get_request_schema(operation)['items'] == {'$ref': '#/components/schemas/XRequest'}
        assert operation['responses']['200'] == {'description': 'No response body'}
    elif ro:
        assert 'requestBody' not in operation
        assert get_response_schema(operation)['items'] == {'$ref': '#/components/schemas/X'}
    else:
        assert get_request_schema(operation)['items'] == {'$ref': '#/components/schemas/XRequest'}
        assert get_response_schema(operation)['items'] == {'$ref': '#/components/schemas/X'}


@mock.patch('drf_spectacular.settings.spectacular_settings.SCHEMA_PATH_PREFIX_INSERT', '/service/backend')
def test_schema_path_prefix_insert(no_warnings):
    @extend_schema(responses=typing.Any)
    @api_view(['GET'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('v1/x/', view_function=view_func)
    assert '/service/backend/v1/x/' in schema['paths']
