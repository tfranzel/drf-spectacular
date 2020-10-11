import re

import pytest
from django.urls import include, path

from drf_spectacular.generators import SchemaGenerator
from tests import assert_schema

transforms = [
    # User model first_name differences
    lambda x: re.sub(r'(first_name:\n *type: string\n *maxLength:) 150', r'\g<1> 30', x, re.M),
    # User model username validator tail
    lambda x: x.replace(r'+$', r'+\Z'),
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
