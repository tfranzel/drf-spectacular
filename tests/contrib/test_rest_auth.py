import pytest
from django.urls import include, path

from drf_spectacular.generators import SchemaGenerator
from tests import assert_schema


@pytest.mark.contrib('rest_auth')
def test_rest_auth(no_warnings):
    urlpatterns = [
        path('rest-auth/', include('rest_auth.urls')),
    ]

    generator = SchemaGenerator(patterns=urlpatterns)
    schema = generator.get_schema(request=None, public=True)

    assert_schema(schema, 'tests/contrib/test_rest_auth.yml')


@pytest.mark.contrib('rest_auth')
def test_rest_auth_registration(no_warnings):
    urlpatterns = [
        path('rest-auth/registration/', include('rest_auth.registration.urls')),
    ]

    generator = SchemaGenerator(patterns=urlpatterns)
    schema = generator.get_schema(request=None, public=True)

    assert_schema(schema, 'tests/contrib/test_rest_auth_registration.yml')
