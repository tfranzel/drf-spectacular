import pytest
from django.urls import path
from rest_framework import mixins, routers, serializers, viewsets

from drf_spectacular.generators import SchemaGenerator
from tests import assert_schema

try:
    from rest_framework_simplejwt.authentication import JWTAuthentication
    from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
except ImportError:
    JWTAuthentication = None


class XSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()


class XViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = XSerializer
    authentication_classes = [JWTAuthentication]
    required_scopes = ['x:read', 'x:write']


@pytest.mark.contrib('rest_framework_simplejwt')
def test_simplejwt(no_warnings):
    router = routers.SimpleRouter()
    router.register('x', XViewset, basename="x")

    urlpatterns = [
        *router.urls,
        path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    ]

    generator = SchemaGenerator(patterns=urlpatterns)
    schema = generator.get_schema(request=None, public=True)

    assert_schema(schema, 'tests/contrib/test_simplejwt.yml')
