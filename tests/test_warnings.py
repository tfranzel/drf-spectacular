from django.db import models
from rest_framework import mixins, serializers, views, viewsets
from rest_framework.authentication import BaseAuthentication
from rest_framework.decorators import action
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema
from tests import generate_schema


def test_serializer_name_reuse(warnings):
    from rest_framework import routers

    from drf_spectacular.generators import SchemaGenerator
    router = routers.SimpleRouter()

    def x1():
        class XSerializer(serializers.Serializer):
            uuid = serializers.UUIDField()

        return XSerializer

    def x2():
        class XSerializer(serializers.Serializer):
            integer = serializers.IntegerField

        return XSerializer

    class X1Viewset(mixins.ListModelMixin, viewsets.GenericViewSet):
        serializer_class = x1()

    router.register('x1', X1Viewset, basename='x1')

    class X2Viewset(mixins.ListModelMixin, viewsets.GenericViewSet):
        serializer_class = x2()

    router.register('x2', X2Viewset, basename='x2')

    generator = SchemaGenerator(patterns=router.urls)
    generator.get_schema(request=None, public=True)


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
    assert 'no queryset' in capsys.readouterr().err


def test_path_param_not_in_model(capsys):
    class M3(models.Model):
        pass  # pragma: no cover

    class XSerializer(serializers.Serializer):
        uuid = serializers.UUIDField()

    class XViewset(viewsets.ReadOnlyModelViewSet):
        serializer_class = XSerializer
        queryset = M3.objects.none()

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


def test_unable_to_follow_field_source_through_intermediate_property_warning(warnings):
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
