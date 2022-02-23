import inspect
import os
from unittest import mock

import pytest
from django.urls import path
from rest_framework.test import APIClient

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(), name='swagger'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(), name='redoc'),
]

BUNDLE_URL = "static/drf_spectacular_sidecar/swagger-ui-dist/swagger-ui-bundle.js"


@mock.patch('drf_spectacular.settings.spectacular_settings.SWAGGER_UI_DIST', 'SIDECAR')
@mock.patch('drf_spectacular.settings.spectacular_settings.SWAGGER_UI_FAVICON_HREF', 'SIDECAR')
@mock.patch('drf_spectacular.settings.spectacular_settings.REDOC_DIST', 'SIDECAR')
@pytest.mark.urls(__name__)
@pytest.mark.contrib('drf_spectacular_sidecar')
def test_sidecar_shortcut_urls_are_resolved(no_warnings):
    response = APIClient().get('/api/schema/swagger-ui/')
    assert b'"/' + BUNDLE_URL.encode() + b'"' in response.content
    assert b'"/static/drf_spectacular_sidecar/swagger-ui-dist/favicon-32x32.png"' in response.content
    response = APIClient().get('/api/schema/redoc/')
    assert b'"/static/drf_spectacular_sidecar/redoc/bundles/redoc.standalone.js"' in response.content


@pytest.mark.contrib('drf_spectacular_sidecar')
def test_sidecar_package_urls_matching(no_warnings):
    # poor man's test to make sure the sidecar package contents match with what
    # collectstatic is going to compile. cannot be tested directly.
    import drf_spectacular_sidecar  # type: ignore[import]
    module_root = os.path.dirname(inspect.getfile(drf_spectacular_sidecar))
    bundle_path = os.path.join(module_root, BUNDLE_URL)
    assert os.path.isfile(bundle_path)
