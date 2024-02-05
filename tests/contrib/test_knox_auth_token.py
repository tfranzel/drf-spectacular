from unittest import mock

import pytest
from rest_framework import mixins, routers, serializers, viewsets

from tests import assert_schema, generate_schema

try:
    from knox.auth import TokenAuthentication
except ImportError:
    TokenAuthentication = None


class XSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()


class XViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = XSerializer
    authentication_classes = [TokenAuthentication]
    required_scopes = ['x:read', 'x:write']


@pytest.mark.contrib('knox_auth_token')
def test_knox_auth_token(no_warnings):
    router = routers.SimpleRouter()
    router.register('x', XViewset, basename="x")

    urlpatterns = [
        *router.urls
    ]

    schema = generate_schema(None, patterns=urlpatterns)

    assert_schema(schema, 'tests/contrib/test_knox_auth_token.yml')


@pytest.mark.contrib('knox_auth_token')
@mock.patch('knox.settings.knox_settings.AUTH_HEADER_PREFIX', 'CustomPrefix')
def test_knox_auth_token_non_default_prefix(no_warnings):
    schema = generate_schema('/x', XViewset)
    assert schema['components']['securitySchemes'] == {
        'knoxApiToken': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Token-based authentication with required prefix "CustomPrefix"'
        },
    }
