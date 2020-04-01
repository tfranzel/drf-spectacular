import os

import pytest
from django.urls import path

from drf_spectacular.validation import validate_schema


def assert_schema(schema, reference_file):
    from drf_spectacular.renderers import NoAliasOpenAPIRenderer

    schema_yml = NoAliasOpenAPIRenderer().render(schema, renderer_context={})

    with open(reference_file.replace('.yml', '_out.yml'), 'wb') as fh:
        fh.write(schema_yml)

    with open(reference_file) as fh:
        assert schema_yml.decode() == fh.read()

    # this is more a less a sanity check as checked-in schemas should be valid anyhow
    validate_schema(schema)


def generate_schema(route, viewset=None, view=None):
    from rest_framework import routers
    from drf_spectacular.openapi import SchemaGenerator

    patterns = []
    if viewset:
        router = routers.SimpleRouter()
        router.register(route, viewset, basename=route)
        patterns = router.urls
    if view:
        patterns = [path(route, view.as_view())]

    generator = SchemaGenerator(patterns=patterns)
    return generator.get_schema(request=None, public=True)


skip_on_travis = pytest.mark.skipif(
    os.environ.get('TRAVIS') == 'true',
    reason="does not work on travis"
)
