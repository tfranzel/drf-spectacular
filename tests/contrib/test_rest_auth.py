import re
from importlib import reload
from unittest import mock

import pytest
from django.urls import include, path
from rest_framework import viewsets

from tests import assert_schema, generate_schema
from tests.models import SimpleModel, SimpleSerializer

transforms = [
    # User model first_name differences
    lambda x: re.sub(r'(first_name:\n *type: string\n *maxLength:) 30', r'\g<1> 150', x, re.M),
]


@pytest.mark.contrib('dj_rest_auth', 'allauth')
@mock.patch('drf_spectacular.settings.spectacular_settings.SCHEMA_PATH_PREFIX', '')
def test_rest_auth(no_warnings):
    urlpatterns = [
        path('rest-auth/', include('dj_rest_auth.urls')),
        path('rest-auth/registration/', include('dj_rest_auth.registration.urls')),
    ]
    schema = generate_schema(None, patterns=urlpatterns)
    assert_schema(
        schema, 'tests/contrib/test_rest_auth.yml', transforms=transforms
    )


@pytest.mark.contrib('dj_rest_auth', 'allauth', 'rest_framework_simplejwt')
@mock.patch('drf_spectacular.settings.spectacular_settings.SCHEMA_PATH_PREFIX', '')
def test_rest_auth_token(no_warnings, settings):
    settings.REST_USE_JWT = True
    # flush module import cache to re-evaluate conditional import
    import dj_rest_auth.urls
    reload(dj_rest_auth.urls)

    urlpatterns = [
        # path('rest-auth/', include(urlpatterns)),
        path('rest-auth/', include('dj_rest_auth.urls')),
        path('rest-auth/registration/', include('dj_rest_auth.registration.urls')),
    ]

    schema = generate_schema(None, patterns=urlpatterns)

    assert_schema(
        schema, 'tests/contrib/test_rest_auth_token.yml', transforms=transforms
    )


@pytest.mark.contrib('dj_rest_auth', 'rest_framework_simplejwt')
@mock.patch('django.conf.settings.JWT_AUTH_COOKIE', 'jwt-session', create=True)
def test_rest_auth_simplejwt_cookie(no_warnings):
    from dj_rest_auth.jwt_auth import JWTCookieAuthentication

    class XViewset(viewsets.ModelViewSet):
        serializer_class = SimpleSerializer
        queryset = SimpleModel.objects.all()
        authentication_classes = [JWTCookieAuthentication]

    schema = generate_schema('/x', XViewset)
    assert schema['paths']['/x/']['get']['security'] == [
        {'jwtHeaderAuth': []}, {'jwtCookieAuth': []}, {}
    ]
    assert schema['components']['securitySchemes'] == {
        'jwtCookieAuth': {'type': 'apiKey', 'in': 'cookie', 'name': 'jwt-session'},
        'jwtHeaderAuth': {'type': 'http', 'scheme': 'bearer', 'bearerFormat': 'JWT'}
    }
