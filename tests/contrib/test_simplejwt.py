from unittest import mock

import pytest
from django.urls import path
from rest_framework import mixins, routers, serializers, viewsets

from tests import assert_schema, generate_schema

try:
    from rest_framework_simplejwt.authentication import (
        JWTAuthentication, JWTTokenUserAuthentication,
    )
    from rest_framework_simplejwt.views import (
        TokenObtainPairView, TokenObtainSlidingView, TokenRefreshView, TokenVerifyView,
    )
except ImportError:
    JWTAuthentication = None


class XSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()


class XViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = XSerializer
    authentication_classes = [JWTAuthentication]
    required_scopes = ['x:read', 'x:write']


class X2Viewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = XSerializer
    authentication_classes = [JWTTokenUserAuthentication]
    required_scopes = ['x:read', 'x:write']


@pytest.mark.contrib('rest_framework_simplejwt')
@pytest.mark.parametrize('view', [XViewset, X2Viewset])
def test_simplejwt(no_warnings, view):
    router = routers.SimpleRouter()
    router.register('x', view, basename="x")

    urlpatterns = [
        *router.urls,
        path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token-sliding/', TokenObtainSlidingView.as_view(), name='token_obtain_sliding'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    ]

    schema = generate_schema(None, patterns=urlpatterns)
    assert_schema(schema, 'tests/contrib/test_simplejwt.yml')


@pytest.mark.contrib('rest_framework_simplejwt')
@mock.patch('rest_framework_simplejwt.settings.api_settings.AUTH_HEADER_TYPES', ('JWT',))
def test_simplejwt_non_bearer_keyword(no_warnings):
    schema = generate_schema('/x', XViewset)
    assert schema['components']['securitySchemes'] == {
        'jwtAuth': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Token-based authentication with required prefix "JWT"'
        }
    }


@pytest.mark.contrib('rest_framework_simplejwt')
@mock.patch(
    'rest_framework_simplejwt.settings.api_settings.AUTH_HEADER_NAME',
    'HTTP_X_TOKEN',
    create=True,
)
def test_simplejwt_non_std_header_name(no_warnings):
    schema = generate_schema('/x', XViewset)
    assert schema['components']['securitySchemes'] == {
        'jwtAuth': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-token',
            'description': 'Token-based authentication with required prefix "Bearer"'
        }
    }
