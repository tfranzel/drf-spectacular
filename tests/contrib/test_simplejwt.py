import pytest
from django.urls import path
from rest_framework import mixins, routers, serializers, viewsets

from tests import assert_schema, generate_schema

try:
    from rest_framework_simplejwt.authentication import (
        JWTAuthentication, JWTTokenUserAuthentication,
    )
    from rest_framework_simplejwt.views import (
        TokenObtainPairView, TokenObtainSlidingView, TokenRefreshView,
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
    ]

    schema = generate_schema(None, patterns=urlpatterns)
    assert_schema(schema, 'tests/contrib/test_simplejwt.yml')
