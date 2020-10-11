import pytest
import yaml
from django.conf.urls import include
from django.db import models
from django.urls import path, re_path
from rest_framework import generics, mixins, routers, serializers, viewsets
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.versioning import AcceptHeaderVersioning, NamespaceVersioning, URLPathVersioning

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


class AcceptHeaderVersioningViewset(PathVersioningViewset):
    versioning_class = AcceptHeaderVersioning


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


class AcceptHeaderVersioningViewset2(PathVersioningViewset2):
    versioning_class = AcceptHeaderVersioning


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


def test_namespace_versioning_urlpatterns_simplification(no_warnings):
    class NamespaceVersioningAPIView(generics.RetrieveUpdateDestroyAPIView):
        versioning_class = NamespaceVersioning
        serializer_class = Xv1Serializer
        queryset = VersioningModel.objects.all()

    urls = (
        path('x/<int:pk>/', NamespaceVersioningAPIView.as_view()),
        path('y/<pk>/', NamespaceVersioningAPIView.as_view()),
        re_path('z/(?P<pk>[0-9A-Fa-f-]+)/', NamespaceVersioningAPIView.as_view()),
    )
    generator = SchemaGenerator(
        patterns=[path('v1/<int:some_param>/', include((urls, 'v1'))), ],
        api_version='v1',
    )
    schema = generator.get_schema(request=None, public=True)

    for s in ['x', 'y', 'z']:
        parameters = schema['paths'][f'/v1/{{some_param}}/{s}/{{id}}/']['get']['parameters']
        parameters = {p['name']: p for p in parameters}
        assert parameters['id']['schema']['type'] == 'integer'
        assert parameters['some_param']['schema']['type'] == 'integer'


@pytest.mark.parametrize('viewset_cls', [AcceptHeaderVersioningViewset, AcceptHeaderVersioningViewset2])
@pytest.mark.parametrize('version', ['v1', 'v2'])
@pytest.mark.parametrize('with_request', [True, False])
def test_accept_header_versioning(no_warnings, viewset_cls, version, with_request):
    router = routers.SimpleRouter()
    router.register('x', viewset_cls, basename='x')
    generator = SchemaGenerator(
        patterns=[
            path('', include((router.urls, 'x'))),
        ],
        api_version=version,
    )
    if with_request:
        view = SpectacularAPIView(
            versioning_class=AcceptHeaderVersioning,
        )
        factory = APIRequestFactory()
        request = factory.get('x', content_type='application/vnd.oai.openapi+json')
        request = view.initialize_request(request)
    else:
        request = None
    schema = generator.get_schema(request=request, public=True)
    assert_schema(schema, f'tests/test_versioning_accept_{version}.yml')


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
urlpatterns_accept_header = [
    path('x/', AcceptHeaderVersioningViewset2.as_view({'get': 'list'})),
    path('schema/', SpectacularAPIView.as_view(
        versioning_class=AcceptHeaderVersioning
    ), name='schema-ahv-versioned'),
    path('schema/ui', SpectacularSwaggerView.as_view(
        versioning_class=AcceptHeaderVersioning, url_name='schema-ahv-versioned'
    )),
]
urlpatterns = [
    # path versioning
    re_path(r'^api/pv/(?P<version>[v1|v2]+)/', include(urlpatterns_path)),
    # namespace versioning
    path('api/nv/v1/', include((urlpatterns_namespace, 'v1'))),
    path('api/nv/v2/', include((urlpatterns_namespace, 'v2'))),
    # accept header versioning
    path('api/ahv/', include((urlpatterns_accept_header, 'x'))),
    # all unversioned
    path('api/schema/', SpectacularAPIView.as_view()),
    # manually versioned schema view that is in itself unversioned
    path('api/schema-v2/', SpectacularAPIView.as_view(api_version='v2')),
]


@pytest.mark.parametrize(['url', 'path_count'], [
    ('/api/nv/v2/schema/', 8),  # v2 nv + v2 pv + v2 ahv + unversioned
    ('/api/pv/v1/schema/', 8),  # v1 nv + v1 pv + v1 ahv + unversioned
    ('/api/schema-v2/', 8),  # v2 nv + v2 pv + v2 ahv + unversioned
    ('/api/schema/', 2),  # unversioned schema
])
@pytest.mark.urls(__name__)
def test_spectacular_view_versioning(no_warnings, url, path_count):
    response = APIClient().get(url)
    assert response.status_code == 200
    schema = yaml.load(response.content, Loader=yaml.SafeLoader)
    validate_schema(schema)
    assert len(schema['paths']) == path_count


@pytest.mark.parametrize('version', ['v1', 'v2'])
@pytest.mark.urls(__name__)
def test_spectacular_view_accept_header_versioning(no_warnings, version):
    response = APIClient().get('/api/ahv/schema/', HTTP_ACCEPT='application/json; version={version}')
    assert response.status_code == 200
    schema = yaml.load(response.content, Loader=yaml.SafeLoader)
    validate_schema(schema)
    assert len(schema['paths']) == 6


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
