from unittest import mock

import pytest
from django import __version__ as DJANGO_VERSION
from django.urls import path
from rest_framework import mixins, routers, serializers, viewsets

from tests import assert_schema, generate_schema

try:
    from rest_framework_jwt.authentication import JSONWebTokenAuthentication
except ImportError:
    JSONWebTokenAuthentication = None


class XSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()


class XViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = XSerializer
    authentication_classes = [JSONWebTokenAuthentication]
    required_scopes = ['x:read', 'x:write']


@pytest.mark.skipif(DJANGO_VERSION >= '4', reason='1.19.1 broken for Django 4.0')
@pytest.mark.contrib('rest_framework_jwt')
def test_drf_jwt(no_warnings):
    from rest_framework_jwt.views import obtain_jwt_token

    router = routers.SimpleRouter()
    router.register('x', XViewset, basename="x")

    urlpatterns = [
        *router.urls,
        path('api-token-auth/', obtain_jwt_token, name='get_token'),
    ]

    schema = generate_schema(None, patterns=urlpatterns)

    assert_schema(schema, 'tests/contrib/test_drf_jwt.yml')


@pytest.mark.skipif(DJANGO_VERSION >= '4', reason='1.19.1 broken for Django 4.0')
@pytest.mark.contrib('rest_framework_jwt')
@mock.patch('rest_framework_jwt.settings.api_settings.JWT_AUTH_HEADER_PREFIX', 'JWT')
def test_drf_jwt_non_bearer_keyword(no_warnings):
    schema = generate_schema('/x', XViewset)
    assert schema['components']['securitySchemes'] == {
        'jwtAuth': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Token-based authentication with required prefix "JWT"'
        },
    }
