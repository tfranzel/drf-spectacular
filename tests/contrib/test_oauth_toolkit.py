from unittest import mock

from django.urls import include, path
from oauth2_provider.contrib.rest_framework import OAuth2Authentication, TokenHasReadWriteScope
from rest_framework import serializers, viewsets, mixins, routers, permissions

from drf_spectacular.generators import SchemaGenerator
from tests import assert_schema


class XSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()


class XViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = XSerializer
    authentication_classes = [OAuth2Authentication]
    permission_classes = [permissions.AllowAny, TokenHasReadWriteScope]
    required_scopes = ['x:read', 'x:write']


@mock.patch(
    'drf_spectacular.settings.spectacular_settings.OAUTH2_FLOWS',
    ['implicit']
)
@mock.patch(
    'drf_spectacular.settings.spectacular_settings.OAUTH2_REFRESH_URL',
    'http://127.0.0.1:8000/o/refresh'
)
@mock.patch(
    'drf_spectacular.settings.spectacular_settings.OAUTH2_AUTHORIZATION_URL',
    'http://127.0.0.1:8000/o/authorize'
)
def test_oauth2_toolkit(no_warnings):
    router = routers.SimpleRouter()
    router.register('x', XViewset, basename="x")

    urlpatterns = [
        *router.urls,
        path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    ]

    generator = SchemaGenerator(patterns=urlpatterns)
    schema = generator.get_schema(request=None, public=True)

    assert_schema(schema, 'tests/contrib/test_oauth_toolkit.yml')
