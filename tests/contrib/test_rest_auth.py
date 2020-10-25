import re
from importlib import reload

import pytest
from django.urls import include, path

from drf_spectacular.generators import SchemaGenerator
from tests import assert_schema

transforms = [
    # User model first_name differences
    lambda x: re.sub(r'(first_name:\n *type: string\n *maxLength:) 30', r'\g<1> 150', x, re.M),
]


@pytest.mark.contrib('dj_rest_auth', 'allauth')
def test_rest_auth(no_warnings):
    urlpatterns = [
        path('rest-auth/', include('dj_rest_auth.urls')),
        path('rest-auth/registration/', include('dj_rest_auth.registration.urls')),
    ]

    generator = SchemaGenerator(patterns=urlpatterns)
    schema = generator.get_schema(request=None, public=True)

    assert_schema(
        schema, 'tests/contrib/test_rest_auth.yml', transforms=transforms
    )


@pytest.mark.contrib('dj_rest_auth', 'allauth', 'rest_framework_simplejwt')
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

    generator = SchemaGenerator(patterns=urlpatterns)
    schema = generator.get_schema(request=None, public=True)

    assert_schema(
        schema, 'tests/contrib/test_rest_auth_token.yml', transforms=transforms
    )
