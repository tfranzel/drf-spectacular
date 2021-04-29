import pytest
import yaml
from django.contrib.auth.models import User
from django.urls import include, path
from rest_framework import routers, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.test import APIClient
from rest_framework.versioning import AcceptHeaderVersioning

from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.views import SpectacularAPIView
from tests.models import SimpleModel, SimpleSerializer


class AnotherSimpleSerializer(SimpleSerializer):
    pass


class XViewset(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = SimpleModel.objects.none()

    def get_serializer_class(self):
        # make sure the mocked request possesses the correct path and
        # schema endpoint path does not leak in.
        assert self.request.path.startswith('/api/x/')
        # make schema dependent on request method
        if self.request.method == 'GET':
            return SimpleSerializer
        else:
            return AnotherSimpleSerializer


router = routers.SimpleRouter()
router.register('x', XViewset)
urlpatterns = [
    path('api/', include(router.urls)),
    path('api/schema-plain/', SpectacularAPIView.as_view()),
    path('api/schema-authenticated/', SpectacularAPIView.as_view(
        authentication_classes=[TokenAuthentication]
    )),
    path('api/schema-authenticated-private/', SpectacularAPIView.as_view(
        authentication_classes=[TokenAuthentication],
        serve_public=False,
    )),
    path('api/schema-versioned/', SpectacularAPIView.as_view(
        versioning_class=AcceptHeaderVersioning
    ))
]


@pytest.mark.urls(__name__)
def test_mock_request_symmetry_plain(no_warnings):
    response = APIClient().get('/api/schema-plain/', **{'HTTP_X_SPECIAL_HEADER': '1'})
    assert response.status_code == 200
    schema_online = yaml.load(response.content, Loader=yaml.SafeLoader)
    schema_offline = SchemaGenerator().get_schema(public=True)
    assert schema_offline == schema_online


@pytest.mark.urls(__name__)
def test_mock_request_symmetry_version(no_warnings):
    response = APIClient().get('/api/schema-versioned/', **{
        'HTTP_ACCEPT': 'application/json; version=v2',
    })
    assert response.status_code == 200
    schema_online = yaml.load(response.content, Loader=yaml.SafeLoader)
    schema_offline = SchemaGenerator(api_version='v2').get_schema(public=True)

    assert schema_offline == schema_online
    assert schema_online['info']['version'] == '0.0.0 (v2)'


@pytest.mark.parametrize(['serve_public', 'authenticated', 'url', 'expected_endpoints'], [
    (True, True, '/api/schema-authenticated/', 5),
    (True, False, '/api/schema-authenticated/', 5),
    (False, True, '/api/schema-authenticated-private/', None),
    (False, False, '/api/schema-authenticated-private/', 3),
])
@pytest.mark.urls(__name__)
@pytest.mark.django_db
def test_mock_request_symmetry_authentication(
        no_warnings, serve_public, authenticated, url, expected_endpoints
):
    user = User.objects.create(username='test')
    token, _ = Token.objects.get_or_create(user=user)
    auth_header = {'HTTP_AUTHORIZATION': f'Token {token}'} if authenticated else {}
    response = APIClient().get(url, **auth_header)
    assert response.status_code == 200

    schema_online = yaml.load(response.content, Loader=yaml.SafeLoader)
    schema_offline = SchemaGenerator().get_schema(public=serve_public)

    if expected_endpoints:
        assert schema_offline == schema_online
        assert len(schema_online['paths']) == expected_endpoints
    else:
        # authenticated & non-public case does not really make sense for
        # offline generation as we have no request.
        assert len(schema_online['paths']) == 5
        assert len(schema_offline['paths']) == 3
