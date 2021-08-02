from unittest import mock

import pytest
from django.urls import include, path
from oauth2_provider.scopes import BaseScopes
from rest_framework import mixins, routers, serializers, viewsets
from rest_framework.authentication import BasicAuthentication

from tests import assert_schema, generate_schema

try:
    from oauth2_provider.contrib.rest_framework import (
        IsAuthenticatedOrTokenHasScope, OAuth2Authentication, TokenHasReadWriteScope,
        TokenHasResourceScope, TokenMatchesOASRequirements,
    )
except ImportError:
    IsAuthenticatedOrTokenHasScope = None
    OAuth2Authentication = None
    TokenHasReadWriteScope = None
    TokenHasResourceScope = None
    TokenMatchesOASRequirements = None


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


class OASRequirementsViewset(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = XSerializer
    authentication_classes = [OAuth2Authentication]
    permission_classes = [TokenMatchesOASRequirements]
    required_alternate_scopes = {
        'GET': [['read']],
        'POST': [['create1', 'scope2'], ['alt-scope3'], ['alt-scope4', 'alt-scope5']],
    }


class TestScopesBackend(BaseScopes):

    def get_all_scopes(self):
        return {'test_backend_scope': 'Test scope for ScopesBackend'}


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
    router.register('OASRequirements', OASRequirementsViewset, basename="x4")

    urlpatterns = [
        *router.urls,
        path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    ]

    schema = generate_schema(None, patterns=urlpatterns)

    assert_schema(schema, 'tests/contrib/test_oauth_toolkit.yml')


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
    'oauth2_provider.settings.oauth2_settings.SCOPES_BACKEND_CLASS',
    TestScopesBackend,
)
@pytest.mark.contrib('oauth2_provider')
def test_oauth2_toolkit_scopes_backend(no_warnings):
    router = routers.SimpleRouter()
    router.register('TokenHasReadWriteScope', TokenHasReadWriteScopeViewset, basename='x')

    urlpatterns = [
        *router.urls,
        path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    ]

    schema = generate_schema(None, patterns=urlpatterns)

    assert 'oauth2' in schema['components']['securitySchemes']
    oauth2 = schema['components']['securitySchemes']['oauth2']
    assert 'implicit' in oauth2['flows']
    flow = oauth2['flows']['implicit']
    assert 'test_backend_scope' in flow['scopes']
