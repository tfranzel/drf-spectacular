import pytest
import yaml
from django.urls import path
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.test import APIClient

from drf_spectacular.utils import extend_schema
from drf_spectacular.views import SpectacularAPIView


def custom_hook(endpoints, **kwargs):
    return [
        (path.rstrip('/'), path_regex.rstrip('/'), method, callback)
        for path, path_regex, method, callback in endpoints
    ]


class XSerializer(serializers.Serializer):
    field = serializers.CharField()


@extend_schema(request=XSerializer, responses=XSerializer)
@api_view(http_method_names=['POST'])
def pi(request):
    return Response(3.1415)  # pragma: no cover


urlpatterns = [
    path('api/pi/', pi),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema-custom/', SpectacularAPIView.as_view(
        custom_settings={
            'TITLE': 'Custom settings with this SpectacularAPIView',
            'SCHEMA_PATH_PREFIX': '',
            'COMPONENT_SPLIT_REQUEST': True,
            'PREPROCESSING_HOOKS': ['tests.test_custom_settings.custom_hook']
        }
    ), name='schema-custom'),
    path('api/schema-invalid/', SpectacularAPIView.as_view(
        custom_settings={'INVALID': 'INVALID'}
    ), name='schema-invalid'),
    path('api/schema-invalid2/', SpectacularAPIView.as_view(
        custom_settings={'SERVE_PUBLIC': 'INVALID'}
    ), name='schema-invalid2'),
]


@pytest.mark.urls(__name__)
def test_custom_settings(no_warnings):
    response = APIClient().get('/api/schema-custom/')
    schema = yaml.load(response.content, Loader=yaml.SafeLoader)
    assert schema['info']['title']
    assert '/api/pi' in schema['paths']  # hook executed
    assert ['api'] == schema['paths']['/api/pi']['post']['tags']  # SCHEMA_PATH_PREFIX
    assert 'XRequest' in schema['components']['schemas']  # COMPONENT_SPLIT_REQUEST

    response = APIClient().get('/api/schema/')
    schema = yaml.load(response.content, Loader=yaml.SafeLoader)
    assert not schema['info']['title']
    assert '/api/pi/' in schema['paths']  # hook not executed
    assert ['pi'] == schema['paths']['/api/pi/']['post']['tags']  # SCHEMA_PATH_PREFIX
    assert 'XRequest' not in schema['components']['schemas']  # COMPONENT_SPLIT_REQUEST


@pytest.mark.urls(__name__)
def test_invalid_custom_settings():
    with pytest.raises(AttributeError):
        APIClient().get('/api/schema-invalid/')
    with pytest.raises(AttributeError):
        APIClient().get('/api/schema-invalid2/')
