import pytest
import yaml
from django.conf.urls import include
from django.db import models
from django.urls import path, re_path
from rest_framework import mixins, routers, serializers, viewsets
from rest_framework.test import APIClient
from rest_framework.versioning import NamespaceVersioning, URLPathVersioning

from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.utils import extend_schema
from drf_spectacular.validation import validate_schema
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from tests import assert_schema


class VersioningModel(models.Model):
    pass


class Xv1Serializer(serializers.Serializer):
    id = serializers.IntegerField()


class Xv2Serializer(serializers.Serializer):
    id = serializers.UUIDField()


class PathVersioningViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    versioning_class = URLPathVersioning
    queryset = VersioningModel.objects.all()

    @extend_schema(responses=Xv1Serializer, versions=['v1'])
    @extend_schema(responses=Xv2Serializer, versions=['v2'])
    def list(self, request, *args, **kwargs):
        pass  # pragma: no cover

    @extend_schema(responses=Xv1Serializer, versions=['v1'])
    @extend_schema(responses=Xv2Serializer, versions=['v2'])
    def retrieve(self, request, *args, **kwargs):
        pass  # pragma: no cover


class NamespaceVersioningViewset(PathVersioningViewset):
    versioning_class = NamespaceVersioning


class PathVersioningViewset2(mixins.ListModelMixin, viewsets.GenericViewSet):
    versioning_class = URLPathVersioning
    queryset = VersioningModel.objects.all()

    def list(self, request, *args, **kwargs):
        pass  # pragma: no cover

    def retrieve(self, request, *args, **kwargs):
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
    path('schema/', SpectacularAPIView.as_view(
        versioning_class=NamespaceVersioning
    ), name='schema-nv-versioned'),
    path('schema/ui', SpectacularSwaggerView.as_view(
        versioning_class=NamespaceVersioning, url_name='schema-nv-versioned'
    )),
]
urlpatterns_path = [
    path('x/', PathVersioningViewset2.as_view({'get': 'list'})),
    path('schema/', SpectacularAPIView.as_view(
        versioning_class=URLPathVersioning
    ), name='schema-pv-versioned'),
    path('schema/ui', SpectacularSwaggerView.as_view(
        versioning_class=URLPathVersioning, url_name='schema-pv-versioned'
    )),
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


@pytest.mark.parametrize(['url', 'schema_url'], [
    ('/api/nv/v1/schema/ui', b'/api/nv/v1/schema/'),
    ('/api/nv/v2/schema/ui', b'/api/nv/v2/schema/'),
    ('/api/pv/v1/schema/ui', b'/api/pv/v1/schema/'),
    ('/api/pv/v2/schema/ui', b'/api/pv/v2/schema/'),
])
@pytest.mark.urls(__name__)
def test_spectacular_ui_view_versioning(no_warnings, url, schema_url):
    response = APIClient().get(url)
    assert schema_url in response.content
