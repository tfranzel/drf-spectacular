from unittest import mock

import pytest
from django.urls import include, path
from rest_framework import mixins, routers, serializers, viewsets
from rest_framework.authentication import BasicAuthentication

from drf_spectacular.generators import SchemaGenerator
from tests import assert_schema

try:
    from oauth2_provider.contrib.rest_framework import (
        IsAuthenticatedOrTokenHasScope, OAuth2Authentication, TokenHasReadWriteScope,
        TokenHasResourceScope,
    )
except ImportError:
    IsAuthenticatedOrTokenHasScope = None
    OAuth2Authentication = None
    TokenHasReadWriteScope = None
    TokenHasResourceScope = None


class XSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()


class TokenHasReadWriteScopeViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = XSerializer
    authentication_classes = [OAuth2Authentication]
    permission_classes = [TokenHasReadWriteScope]
    # required_scopes is not mandatory here


class TokenHasResourceScopeViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = XSerializer
    authentication_classes = [OAuth2Authentication]
    permission_classes = [TokenHasResourceScope]
    required_scopes = ['extra_scope']


class IsAuthenticatedOrTokenHasScopeViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = XSerializer
    authentication_classes = [OAuth2Authentication, BasicAuthentication]
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ['extra_scope']


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
@mock.patch(
    'oauth2_provider.settings.oauth2_settings.SCOPES',
    {"read": "Reading scope", "write": "Writing scope", "extra_scope": "Extra Scope"},
)
@mock.patch(
    'oauth2_provider.settings.oauth2_settings.DEFAULT_SCOPES',
    ["read", "write"]
)
@pytest.mark.contrib('oauth2_provider')
def test_oauth2_toolkit(no_warnings):
    router = routers.SimpleRouter()
    router.register('TokenHasReadWriteScope', TokenHasReadWriteScopeViewset, basename="x1")
    router.register('TokenHasResourceScope', TokenHasResourceScopeViewset, basename="x2")
    router.register('IsAuthenticatedOrTokenHasScope', IsAuthenticatedOrTokenHasScopeViewset, basename="x3")

    urlpatterns = [
        *router.urls,
        path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    ]

    generator = SchemaGenerator(patterns=urlpatterns)
    schema = generator.get_schema(request=None, public=True)

    assert_schema(schema, 'tests/contrib/test_oauth_toolkit.yml')
