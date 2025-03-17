import re
from importlib import reload
from unittest import mock

import pytest
from django.urls import include, path
from rest_framework import viewsets

from tests import assert_schema, generate_schema, get_request_schema
from tests.models import SimpleModel, SimpleSerializer

try:
    from allauth import __version__ as allauth_version
    from dj_rest_auth.__version__ import __version__ as dj_rest_auth_version
except ImportError:
    dj_rest_auth_version = ""
    allauth_version = ""

transforms = [
    # User model first_name differences
    lambda x: re.sub(r'(first_name:\n *type: string\n *maxLength:) 30', r'\g<1> 150', x),
    # Ignore descriptions as it varies too much between versions
    lambda x: re.sub(r'description: \|-\n[\S\s\r\n]+?tags:', r'tags:', x),
]


@pytest.mark.skipif(dj_rest_auth_version < "5" and allauth_version >= "0.55.0", reason='')
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


@pytest.mark.skipif(dj_rest_auth_version < "5" and allauth_version >= "0.55.0", reason='')
@pytest.mark.contrib('dj_rest_auth', 'allauth', 'rest_framework_simplejwt')
@mock.patch('drf_spectacular.settings.spectacular_settings.SCHEMA_PATH_PREFIX', '')
@mock.patch('dj_rest_auth.app_settings.api_settings.USE_JWT', True)
def test_rest_auth_token(no_warnings, settings):
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
@mock.patch('dj_rest_auth.app_settings.api_settings.JWT_AUTH_COOKIE', 'jwt-session', create=True)
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


@pytest.mark.contrib('dj_rest_auth', 'rest_framework_simplejwt')
@mock.patch('dj_rest_auth.app_settings.api_settings.USE_JWT', True, create=True)
def test_rest_auth_token_blacklist(no_warnings, settings):
    # flush module import cache to re-evaluate conditional import
    import dj_rest_auth.urls
    reload(dj_rest_auth.urls)

    settings.INSTALLED_APPS += (
        'rest_framework_simplejwt',
        'rest_framework_simplejwt.token_blacklist',
    )
    settings.SIMPLE_JWT = {
        'BLACKLIST_AFTER_ROTATION': True
    }

    urlpatterns = [
        path('rest-auth/', include('dj_rest_auth.urls')),
    ]
    schema = generate_schema(None, patterns=urlpatterns)
    assert get_request_schema(schema['paths']['/rest-auth/logout/']['post'])['$ref'] == '#/components/schemas/Logout'
    assert schema['components']['schemas']['Logout'] == {
        'type': 'object',
        'properties': {
            'refresh': {
                'type': 'string',
            },
        },
        'required': [
            'refresh',
        ],
    }
