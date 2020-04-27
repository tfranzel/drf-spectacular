import pytest
import yaml
from django.conf.urls import url
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.test import APIClient

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from drf_spectacular.validation import validate_schema
from drf_spectacular.views import SpectacularAPIView


@extend_schema(responses=OpenApiTypes.FLOAT)
@api_view(http_method_names=['GET'])
def pi(request):
    return Response(3.1415)


urlpatterns_v1 = [url(r'^api/v1/pi', pi)]
urlpatterns_v1.append(
    url(r'^api/v1/schema$', SpectacularAPIView.as_view(urlconf=urlpatterns_v1))
)

urlpatterns_v2 = [
    url(r'^api/v2/pi', pi),
    url(r'^api/v2/pi-fast', pi),
]
urlpatterns_v2.append(
    url(r'^api/v2/schema$', SpectacularAPIView.as_view(urlconf=urlpatterns_v2)),
)

urlpatterns = urlpatterns_v1 + urlpatterns_v2


@pytest.mark.urls(__name__)
def test_spectacular_view(no_warnings):
    response = APIClient().get('/api/v1/schema')
    assert response.status_code == 200
    assert response.content.startswith(b'openapi: 3.0.3\n')
    assert response.accepted_media_type == 'application/vnd.oai.openapi'

    schema = yaml.load(response.content, Loader=yaml.SafeLoader)
    validate_schema(schema)
    assert len(schema['paths']) == 2


@pytest.mark.urls(__name__)
def test_spectacular_view_custom_urlconf(no_warnings):
    response = APIClient().get('/api/v2/schema')
    assert response.status_code == 200

    schema = yaml.load(response.content, Loader=yaml.SafeLoader)
    validate_schema(schema)
    assert len(schema['paths']) == 3

    response = APIClient().get('/api/v2/pi-fast')
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
    response = APIClient().get('/api/v1/schema', HTTP_ACCEPT=accept)
    assert response.status_code == 200
    assert response.accepted_media_type == accept
    if format == 'json':
        assert response.content.startswith(b'{\n' + indent * b' ' + b'"openapi": "3.0.3"')
    if format == 'yaml':
        assert response.content.startswith(b'openapi: 3.0.3\n')
