import os

import pytest


def assert_schema(schema, reference_file):
    from drf_spectacular.renderers import NoAliasOpenAPIRenderer

    schema_yml = NoAliasOpenAPIRenderer().render(schema, renderer_context={})

    with open(reference_file.replace('.yml', '_out.yml'), 'wb') as fh:
        fh.write(schema_yml)

    with open(reference_file) as fh:
        assert schema_yml.decode() == fh.read()


def generate_schema(route, viewset):
    from rest_framework import routers
    from drf_spectacular.openapi import SchemaGenerator

    router = routers.SimpleRouter()
    router.register(route, viewset, basename=route)
    generator = SchemaGenerator(patterns=router.urls)
    return generator.get_schema(request=None, public=True)


skip_on_travis = pytest.mark.skipif(
    os.environ.get('TRAVIS') == 'true',
    reason="does not work on travis"
)
