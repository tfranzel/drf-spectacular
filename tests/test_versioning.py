import pytest
import yaml
from django.conf.urls import include
from django.urls import path, re_path
from rest_framework import routers
from rest_framework import serializers, mixins, viewsets
from rest_framework.test import APIClient
from rest_framework.versioning import URLPathVersioning, NamespaceVersioning

from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.utils import extend_schema
from drf_spectacular.validation import validate_schema
from drf_spectacular.views import SpectacularAPIView
from tests import assert_schema


class Xv1Serializer(serializers.Serializer):
    id = serializers.IntegerField()


class Xv2Serializer(serializers.Serializer):
    id = serializers.UUIDField()


class PathVersioningViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    versioning_class = URLPathVersioning

    @extend_schema(request=Xv1Serializer, responses=Xv1Serializer, versions=['v1'])
    @extend_schema(request=Xv2Serializer, responses=Xv2Serializer, versions=['v2'])
    def list(self, request, *args, **kwargs):
        pass  # pragma: no cover


class NamespaceVersioningViewset(PathVersioningViewset):
    versioning_class = NamespaceVersioning


class PathVersioningViewset2(mixins.ListModelMixin, viewsets.GenericViewSet):
    versioning_class = URLPathVersioning

    def list(self, request, *args, **kwargs):
        pass  # pragma: no cover

    def get_serializer_class(self):
        if self.request.version == 'v2':
            return Xv2Serializer
        return Xv1Serializer


class NamespaceVersioningViewset2(PathVersioningViewset2):
    versioning_class = NamespaceVersioning


@pytest.mark.parametrize('viewset_cls', [PathVersioningViewset, PathVersioningViewset2])
@pytest.mark.parametrize('version', ['v1', 'v2'])
def test_url_path_versioning(no_warnings, viewset_cls, version):
    router = routers.SimpleRouter()
    router.register('x', viewset_cls, basename='x')
    generator = SchemaGenerator(
        patterns=[re_path(r'^(?P<version>[v1|v2]+)/', include((router.urls, 'x')))],
        api_version=version,
    )
    schema = generator.get_schema(request=None, public=True)
    assert_schema(schema, f'tests/test_versioning_{version}.yml')


@pytest.mark.parametrize('viewset_cls', [NamespaceVersioningViewset, NamespaceVersioningViewset2])
@pytest.mark.parametrize('version', ['v1', 'v2'])
def test_namespace_versioning(no_warnings, viewset_cls, version):
    router = routers.SimpleRouter()
    router.register('x', viewset_cls, basename='x')
    generator = SchemaGenerator(
        patterns=[
            path('v1/', include((router.urls, 'v1'))),
            path('v2/', include((router.urls, 'v2'))),
        ],
        api_version=version,
    )
    schema = generator.get_schema(request=None, public=True)
    assert_schema(schema, f'tests/test_versioning_{version}.yml')


urlpatterns_namespace = [
    path('x/', NamespaceVersioningViewset.as_view({'get': 'list'})),
    path('schema/', SpectacularAPIView.as_view(versioning_class=NamespaceVersioning)),
]
urlpatterns_path = [
    path('x/', PathVersioningViewset2.as_view({'get': 'list'})),
    path('schema/', SpectacularAPIView.as_view(versioning_class=URLPathVersioning)),
]
urlpatterns = [
    # path versioning
    re_path(r'^api/pv/(?P<version>[v1|v2]+)/', include(urlpatterns_path)),
    # namespace versioning
    path('api/nv/v1/', include((urlpatterns_namespace, 'v1'))),
    path('api/nv/v2/', include((urlpatterns_namespace, 'v2'))),
    # all unversioned
    path('api/schema/', SpectacularAPIView.as_view()),
    # manually versioned schema view that is in itself unversioned
    path('api/schema-v2/', SpectacularAPIView.as_view(api_version='v2')),
]


@pytest.mark.parametrize(['url', 'path_count'], [
    ('/api/nv/v2/schema/', 6),  # v2 nv + v2 pv + unversioned
    ('/api/pv/v1/schema/', 6),  # v1 nv + v1 pv + unversioned
    ('/api/schema-v2/', 6),  # v2 nv + v2 pv + unversioned
    ('/api/schema/', 2),  # unversioned schema
])
@pytest.mark.urls(__name__)
def test_spectacular_view_versioning(no_warnings, url, path_count):
    response = APIClient().get(url)
    assert response.status_code == 200
    schema = yaml.load(response.content, Loader=yaml.SafeLoader)
    validate_schema(schema)
    assert len(schema['paths']) == path_count
