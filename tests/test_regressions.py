import uuid
from unittest import mock

import pytest
from django.core import validators
from django.db import models
from django.db.models import fields
from django.urls import path, re_path
from rest_framework import (
    filters, generics, mixins, pagination, parsers, routers, serializers, views, viewsets,
)
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action, api_view
from rest_framework.views import APIView

from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.hooks import preprocess_exclude_path_format
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter, extend_schema, extend_schema_field, extend_schema_serializer,
    extend_schema_view, inline_serializer,
)
from drf_spectacular.validation import validate_schema
from tests import generate_schema, get_request_schema, get_response_schema
from tests.models import SimpleModel, SimpleSerializer


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

    generator = SchemaGenerator(patterns=[
        re_path(r'^x$', XAPIView.as_view(), name='x'),
        re_path(r'^y$', YAPIView.as_view(), name='y'),
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
        re_path(r'^x$', XAPIView.as_view(), name='x'),
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

    generator = SchemaGenerator(patterns=urlpatterns)
    schema = generator.get_schema(request=None, public=True)
    validate_schema(schema)

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
    generator = SchemaGenerator(patterns=urlpatterns)
    schema = generator.get_schema(request=None, public=True)
    validate_schema(schema)
    assert list(schema['paths'].keys()) == ['/pi']


def test_regex_path_parameter_discovery(no_warnings):
    @extend_schema(responses=OpenApiTypes.FLOAT)
    @api_view(['GET'])
    def pi(request, foo):
        pass  # pragma: no cover

    urlpatterns = [re_path(r'^/pi/<int:precision>', pi)]
    generator = SchemaGenerator(patterns=urlpatterns)
    schema = generator.get_schema(request=None, public=True)
    validate_schema(schema)
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
            return  # pragma: no cover

        def func(self) -> FieldSourceTraversalModel2:  # property is required for traversal
            return  # pragma: no cover

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

    def enveloper(serializer_class, list):
        @extend_schema_serializer(many=False)
        class EnvelopeSerializer(serializers.Serializer):
            status = serializers.BooleanField()
            data = XSerializer(many=list)

            class Meta:
                ref_name = 'Enveloped{}{}'.format(
                    serializer_class.__name__.replace("Serializer", ""),
                    "List" if list else "",
                )
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
    assert schema['components']['schemas']['X']['properties']['field_m2m_ro']['readOnly'] is True
    # readOnly only needed on outer object, not in items
    assert 'readOnly' not in schema['components']['schemas']['X']['properties']['field_m2m_ro']['items']
    assert 'readOnly' not in schema['components']['schemas']['X']['properties']['field_m2m']


def test_extension_subclass_discovery(no_warnings):
    from rest_framework.authentication import TokenAuthentication

    class CustomAuth(TokenAuthentication):
        pass

    class XSerializer(serializers.Serializer):
        field = serializers.IntegerField

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
    generator = SchemaGenerator(patterns=urlpatterns)
    schema = generator.get_schema(request=None, public=True)
    validate_schema(schema)
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
            return SimpleSerializer

        def get_queryset(self):
            assert not self.request.user.is_authenticated
            assert self.request.method == 'GET'
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
    generator = SchemaGenerator(patterns=router.urls)
    schema = generator.get_schema(request=None, public=True)
    validate_schema(schema)


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
        field = fields.IntegerField()

    class XViewset(viewsets.ViewSet):
        serializer_class = XSerializer

        def retrieve(self, request, *args, **kwargs):
            pass  # pragma: no cover

    urlpatterns = [
        path("api/<path:some_var>/<uuid:pk>/", XViewset.as_view({"get": "retrieve"}))
    ]
    generator = SchemaGenerator(patterns=urlpatterns)
    schema = generator.get_schema(request=None, public=True)
    validate_schema(schema)
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


def test_manual_decimal_validator():
    # manually test this validator as it is not part of the default workflow
    class XSerializer(serializers.Serializer):
        field = serializers.CharField(
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


@pytest.mark.parametrize('path', [
    r'x/(?P<related_field>[0-9a-f-]{36})/',
    r'x/<related_field>/',
])
def test_path_param_from_related_model_pk_without_primary_key_true(no_warnings, path):
    class M3(models.Model):
        related_field = models.ForeignKey(SimpleModel, on_delete=models.PROTECT, editable=False)
        many_related = models.ManyToManyField(SimpleModel)

    class M3Serializer(serializers.ModelSerializer):
        class Meta:
            fields = '__all__'
            model = M3

    class XViewset(viewsets.ModelViewSet):
        serializer_class = M3Serializer
        queryset = M3.objects.none()

    router = routers.SimpleRouter()
    router.register(path, XViewset)

    schema = SchemaGenerator(patterns=router.urls).get_schema(request=None, public=True)
    assert '/x/{related_field}/' in schema['paths']
    assert '/x/{related_field}/{id}/' in schema['paths']
