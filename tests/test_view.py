from unittest import mock

import pytest
import yaml
from django import __version__ as DJANGO_VERSION
from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.test import APIClient

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from drf_spectacular.validation import validate_schema
from drf_spectacular.views import (
    SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerSplitView, SpectacularSwaggerView,
)


@extend_schema(responses=OpenApiTypes.FLOAT)
@api_view(http_method_names=['GET'])
def pi(request):
    return Response(3.1415)


urlpatterns_v1 = [path('api/v1/pi/', pi)]
urlpatterns_v1.append(
    path('api/v1/schema/', SpectacularAPIView.as_view(urlconf=urlpatterns_v1))
)

urlpatterns_v2 = [
    path('api/v2/pi/', pi),
    path('api/v2/pi-fast/', pi),
    path('api/v2/schema/swagger-ui/', SpectacularSwaggerView.as_view(), name='swagger'),
    path('api/v2/schema/swagger-ui-alt/', SpectacularSwaggerSplitView.as_view(), name='swagger-alt'),
    path('api/v2/schema/redoc/', SpectacularRedocView.as_view(), name='redoc'),
]
urlpatterns_v2.append(
    path('api/v2/schema/', SpectacularAPIView.as_view(urlconf=urlpatterns_v2), name='schema'),
)
urlpatterns_str_import = [
    path('api/schema-str1/', SpectacularAPIView.as_view(urlconf=['tests.test_view']), name='schema_str1'),
    path('api/schema-str2/', SpectacularAPIView.as_view(urlconf='tests.test_view'), name='schema_str2'),
    path('api/schema-err1/', SpectacularAPIView.as_view(urlconf=['tests.error']), name='schema_err1'),
    path('api/schema-err2/', SpectacularAPIView.as_view(urlconf='tests.error'), name='schema_err2'),
]

urlpatterns = urlpatterns_v1 + urlpatterns_v2 + urlpatterns_str_import


@pytest.mark.urls(__name__)
def test_spectacular_view(no_warnings):
    response = APIClient().get('/api/v1/schema/')
    assert response.status_code == 200
    assert response.content.startswith(b'openapi: 3.0.3\n')
    assert response.accepted_media_type == 'application/vnd.oai.openapi'

    if DJANGO_VERSION > '3':
        assert response.headers.get('CONTENT-DISPOSITION') == 'inline; filename="schema.yaml"'

    schema = yaml.load(response.content, Loader=yaml.SafeLoader)
    validate_schema(schema)
    assert len(schema['paths']) == 2


@pytest.mark.urls(__name__)
def test_spectacular_view_custom_urlconf(no_warnings):
    response = APIClient().get('/api/v2/schema/')
    assert response.status_code == 200

    schema = yaml.load(response.content, Loader=yaml.SafeLoader)
    validate_schema(schema)
    assert len(schema['paths']) == 3

    response = APIClient().get('/api/v2/pi-fast/')
    assert response.status_code == 200
    assert response.content == b'3.1415'


@pytest.mark.parametrize(['accept', 'format', 'indent'], [
    ('application/vnd.oai.openapi', 'yaml', None),
    ('application/yaml', 'yaml', None),
    ('application/vnd.oai.openapi+json', 'json', 4),
    ('application/json', 'json', 4),
    ('application/json; indent=8', 'json', 8),
])
@pytest.mark.urls(__name__)
def test_spectacular_view_accept(accept, format, indent):
    response = APIClient().get('/api/v1/schema/', HTTP_ACCEPT=accept)
    assert response.status_code == 200
    assert response.accepted_media_type == accept
    if format == 'json':
        assert response.content.startswith(b'{\n' + indent * b' ' + b'"openapi": "3.0.3"')
    if format == 'yaml':
        assert response.content.startswith(b'openapi: 3.0.3\n')


@pytest.mark.urls(__name__)
def test_spectacular_view_accept_unknown(no_warnings):
    response = APIClient().get('/api/v1/schema/', HTTP_ACCEPT='application/unknown')
    assert response.status_code == 406
    assert response.content == (
        b'detail:\n  string: Could not satisfy the request Accept header.\n'
        b'  code: not_acceptable\n'
    )


@pytest.mark.parametrize('ui', ['redoc', 'swagger-ui'])
@pytest.mark.urls(__name__)
def test_spectacular_ui_view(no_warnings, ui):
    from drf_spectacular.settings import spectacular_settings
    response = APIClient().get(f'/api/v2/schema/{ui}/')
    assert response.status_code == 200
    assert response.content.startswith(b'<!DOCTYPE html>')
    if ui == 'redoc':
        assert b'<title>Redoc</title>' in response.content
        assert spectacular_settings.REDOC_DIST.encode() in response.content
    else:
        assert b'<title>Swagger</title>' in response.content
        assert spectacular_settings.SWAGGER_UI_DIST.encode() in response.content
    assert b'"/api/v2/schema/"' in response.content


@pytest.mark.urls(__name__)
def test_spectacular_swagger_ui_alternate(no_warnings):
    # first request for the html
    response = APIClient().get('/api/v2/schema/swagger-ui-alt/')
    assert response.status_code == 200
    assert response.content.startswith(b'<!DOCTYPE html>')
    assert b'"/api/v2/schema/swagger-ui-alt/?script="' in response.content
    # second request to obtain js swagger config (CSP self)
    response = APIClient().get('/api/v2/schema/swagger-ui-alt/?script=')
    assert response.status_code == 200
    assert b'"/api/v2/schema/"' in response.content


@mock.patch(
    'drf_spectacular.settings.spectacular_settings.SWAGGER_UI_SETTINGS',
    '{"deepLinking": true}'
)
@pytest.mark.urls(__name__)
def test_spectacular_ui_with_raw_settings(no_warnings):
    response = APIClient().get('/api/v2/schema/swagger-ui/')
    assert response.status_code == 200
    assert b'const swaggerSettings = {"deepLinking": true};\n' in response.content


@pytest.mark.urls(__name__)
def test_spectacular_ui_param_passthrough(no_warnings):
    response = APIClient().get('/api/v2/schema/swagger-ui/?foo=bar&lang=jp&version=v2')
    assert response.status_code == 200
    assert b'url: "/api/v2/schema/?lang\\u003Djp\\u0026version\\u003Dv2"' in response.content


@pytest.mark.parametrize('url', ['/api/schema-str1/', '/api/schema-str2/'])
@pytest.mark.urls(__name__)
def test_spectacular_urlconf_module_list_import(no_warnings, url):
    response = APIClient().get(url)
    assert response.status_code == 200
    assert b'/api/v1/pi/' in response.content
    assert b'/api/v2/pi/' in response.content


@pytest.mark.parametrize('url', ['/api/schema-err1/', '/api/schema-err2/'])
@pytest.mark.urls(__name__)
def test_spectacular_urlconf_module_list_import_error(no_warnings, url):
    with pytest.raises(ModuleNotFoundError):
        APIClient().get(url)
