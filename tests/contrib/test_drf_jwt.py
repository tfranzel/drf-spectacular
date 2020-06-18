import pytest
from django.urls import path
from rest_framework import mixins, routers, serializers, viewsets

from drf_spectacular.generators import SchemaGenerator
from tests import assert_schema

try:
    from rest_framework_jwt.authentication import JSONWebTokenAuthentication
    from rest_framework_jwt.views import obtain_jwt_token
except ImportError:
    JSONWebTokenAuthentication = None


class XSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()


class XViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = XSerializer
    authentication_classes = [JSONWebTokenAuthentication]
    required_scopes = ['x:read', 'x:write']


@pytest.mark.contrib('rest_framework_jwt')
def test_drf_jwt(no_warnings):
    router = routers.SimpleRouter()
    router.register('x', XViewset, basename="x")

    urlpatterns = [
        *router.urls,
        path('api-token-auth/', obtain_jwt_token, name='get_token'),
    ]

    generator = SchemaGenerator(patterns=urlpatterns)
    schema = generator.get_schema(request=None, public=True)

    assert_schema(schema, 'tests/contrib/test_drf_jwt.yml')
