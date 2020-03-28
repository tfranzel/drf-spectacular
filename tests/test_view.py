import pytest
import yaml
from django.conf.urls import url
from rest_framework.test import APIClient

from drf_spectacular.validation import validate_schema
from drf_spectacular.views import SpectacularAPIView

urlpatterns = [url(r'^api/schema$', SpectacularAPIView.as_view(), name='schema')]


@pytest.mark.urls(__name__)
def test_spectacular_view(no_warnings):
    response = APIClient().get('/api/schema')
    assert response.status_code == 200
    assert response.content.startswith(b'openapi: 3.0.3\n')
    assert response.accepted_media_type == 'application/vnd.oai.openapi'
    schema = yaml.load(response.content, Loader=yaml.SafeLoader)
    validate_schema(schema)
