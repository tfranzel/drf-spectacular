from unittest import mock

import pytest
from django.db import models
from django.urls import path
from rest_framework import mixins, serializers, views, viewsets
from rest_framework.authentication import BaseAuthentication
from rest_framework.decorators import action, api_view
from rest_framework.schemas import AutoSchema as DRFAutoSchema
from rest_framework.views import APIView

from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema, extend_schema_view
from tests import generate_schema
from tests.models import SimpleModel, SimpleSerializer


def test_serializer_name_reuse(capsys):
    from rest_framework import routers

    from drf_spectacular.generators import SchemaGenerator
    router = routers.SimpleRouter()

    def x1():
        class XSerializer(serializers.Serializer):
            uuid = serializers.UUIDField()

        return XSerializer

    def x2():
        class XSerializer(serializers.Serializer):
            integer = serializers.IntegerField()

        return XSerializer

    class X1Viewset(mixins.ListModelMixin, viewsets.GenericViewSet):
        serializer_class = x1()

    router.register('x1', X1Viewset, basename='x1')

    class X2Viewset(mixins.ListModelMixin, viewsets.GenericViewSet):
        serializer_class = x2()

    router.register('x2', X2Viewset, basename='x2')

    generator = SchemaGenerator(patterns=router.urls)
    generator.get_schema(request=None, public=True)

    stderr = capsys.readouterr().err
    assert 'Encountered 2 components with identical names "X" and different classes' in stderr


def test_owned_serializer_naming_override_with_ref_name_collision(warnings):
    class XSerializer(serializers.Serializer):
        x = serializers.UUIDField()

    class YSerializer(serializers.Serializer):
        x = serializers.IntegerField()

        class Meta:
            ref_name = 'X'  # already used above

    class XAPIView(APIView):
        @extend_schema(request=XSerializer, responses=YSerializer)
        def post(self, request):
            pass  # pragma: no cover

    generate_schema('x', view=XAPIView)


def test_no_queryset_warn(capsys):
    class X1Serializer(serializers.Serializer):
        uuid = serializers.UUIDField()

    class X1Viewset(viewsets.ReadOnlyModelViewSet):
        serializer_class = X1Serializer

    generate_schema('x1', X1Viewset)
    stderr = capsys.readouterr().err
    assert 'obtaining queryset from' in stderr  # warning 1
    assert 'failed to obtain model through view\'s queryset' in stderr  # warning 2


def test_path_param_not_in_model(capsys):
    class XViewset(viewsets.ReadOnlyModelViewSet):
        serializer_class = SimpleSerializer
        queryset = SimpleModel.objects.none()

        @action(detail=True, url_path='meta/(?P<ephemeral>[^/.]+)', methods=['POST'])
        def meta_param(self, request, ephemeral, pk):
            pass  # pragma: no cover

    generate_schema('x1', XViewset)
    assert 'no such field' in capsys.readouterr().err


def test_no_authentication_scheme_registered(capsys):
    class XAuth(BaseAuthentication):
        pass  # pragma: no cover

    class XSerializer(serializers.Serializer):
        uuid = serializers.UUIDField()

    class XViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
        serializer_class = XSerializer
        authentication_classes = [XAuth]

    generate_schema('x', XViewset)
    assert 'no OpenApiAuthenticationExtension registered' in capsys.readouterr().err


def test_serializer_not_found(capsys):
    class XViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
        pass  # pragma: no cover

    generate_schema('x', XViewset)
    assert 'Exception raised while getting serializer' in capsys.readouterr().err


def test_extend_schema_unknown_class(capsys):
    class DoesNotCompute:
        pass  # pragma: no cover

    class X1Viewset(viewsets.GenericViewSet):
        @extend_schema(responses={200: DoesNotCompute})
        def list(self, request):
            pass  # pragma: no cover

    generate_schema('x1', X1Viewset)
    assert 'Expected either a serializer' in capsys.readouterr().err


def test_extend_schema_unknown_class2(capsys):
    class DoesNotCompute:
        pass  # pragma: no cover

    class X1Viewset(viewsets.GenericViewSet):
        @extend_schema(responses=DoesNotCompute)
        def list(self, request):
            pass  # pragma: no cover

    generate_schema('x1', X1Viewset)
    assert 'Expected either a serializer' in capsys.readouterr().err


def test_no_serializer_class_on_apiview(capsys):
    class XView(views.APIView):
        def get(self, request):
            pass  # pragma: no cover

    generate_schema('x', view=XView)
    assert 'Unable to guess serializer for' in capsys.readouterr().err


def test_unable_to_follow_field_source_through_intermediate_property_warning(capsys):
    class FailingFieldSourceTraversalModel1(models.Model):
        @property
        def x(self):  # missing type hint emits warning
            return  # pragma: no cover

    class XSerializer(serializers.ModelSerializer):
        x = serializers.ReadOnlyField(source='x.y')

        class Meta:
            model = FailingFieldSourceTraversalModel1
            fields = '__all__'

    class XAPIView(APIView):
        @extend_schema(responses=XSerializer)
        def get(self, request):
            pass  # pragma: no cover

    generate_schema('x', view=XAPIView)
    assert (
        'could not follow field source through intermediate property'
    ) in capsys.readouterr().err


def test_unable_to_derive_function_type_warning(capsys):
    class FailingFieldSourceTraversalModel2(models.Model):
        @property
        def x(self):  # missing type hint emits warning
            return  # pragma: no cover

    class XSerializer(serializers.ModelSerializer):
        x = serializers.ReadOnlyField()
        y = serializers.SerializerMethodField()

        def get_y(self):
            return  # pragma: no cover

        class Meta:
            model = FailingFieldSourceTraversalModel2
            fields = '__all__'

    class XAPIView(APIView):
        @extend_schema(responses=XSerializer)
        def get(self, request):
            pass  # pragma: no cover

    generate_schema('x', view=XAPIView)
    stderr = capsys.readouterr().err
    assert 'unable to resolve type hint for function "x"' in stderr
    assert 'unable to resolve type hint for function "get_y"' in stderr


def test_operation_id_collision_resolution(capsys):
    @extend_schema(responses=OpenApiTypes.FLOAT)
    @api_view(['GET'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    urlpatterns = [
        path('pi/<int:foo>', view_func),
        path('pi/', view_func),
    ]
    generator = SchemaGenerator(patterns=urlpatterns)
    schema = generator.get_schema(request=None, public=True)

    assert schema['paths']['/pi/']['get']['operationId'] == 'pi_retrieve'
    assert schema['paths']['/pi/{foo}']['get']['operationId'] == 'pi_retrieve_2'
    assert 'operationId "pi_retrieve" has collisions' in capsys.readouterr().err


@mock.patch('rest_framework.settings.api_settings.DEFAULT_SCHEMA_CLASS', DRFAutoSchema)
def test_compatible_auto_schema_class_on_view(no_warnings):
    @extend_schema(responses=OpenApiTypes.FLOAT)
    @api_view(['GET'])
    def view_func(request):
        pass  # pragma: no cover

    with pytest.raises(AssertionError) as excinfo:
        generate_schema('/x/', view_function=view_func)
    assert "Incompatible AutoSchema" in str(excinfo.value)


def test_extend_schema_view_on_missing_view_method(capsys):
    @extend_schema_view(
        post=extend_schema(tags=['tag'])
    )
    class XAPIView(APIView):
        def get(self, request):
            pass  # pragma: no cover

    generate_schema('x', view=XAPIView)
    stderr = capsys.readouterr().err
    assert '@extend_schema_view argument "post" was not found on view' in stderr


def test_polymorphic_proxy_subserializer_missing_type_field(capsys):
    class IncompleteSerializer(serializers.Serializer):
        field = serializers.IntegerField()  # missing field named type

    class XAPIView(APIView):
        @extend_schema(
            responses=PolymorphicProxySerializer(
                component_name='Broken',
                serializers=[IncompleteSerializer],
                resource_type_field_name='type',
            )
        )
        def get(self, request):
            pass  # pragma: no cover

    generate_schema('x', view=XAPIView)
    stderr = capsys.readouterr().err
    assert 'sub-serializer Incomplete of Broken must contain' in stderr


def test_warning_operation_id_on_extend_schema_view(capsys):
    @extend_schema(operation_id='Invalid', responses=int)
    class XAPIView(APIView):
        def get(self, request):
            pass  # pragma: no cover

    generate_schema('x', view=XAPIView)
    stderr = capsys.readouterr().err
    assert 'using @extend_schema on viewset class XAPIView with parameters' in stderr


def test_warning_request_body_not_resolvable(capsys):
    class Dummy:
        pass

    @extend_schema(request=Dummy)
    @api_view(['POST'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    generate_schema('x', view_function=view_func)
    stderr = capsys.readouterr().err
    assert 'could not resolve request body for POST /x' in stderr
