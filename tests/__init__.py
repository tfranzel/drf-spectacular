import difflib
import os

from drf_spectacular.validation import validate_schema


def assert_schema(schema, reference_filename, transforms=None):
    from drf_spectacular.renderers import OpenApiJsonRenderer, OpenApiYamlRenderer

    schema_yml = OpenApiYamlRenderer().render(schema, renderer_context={})
    # render also a json and provoke serialization issues
    OpenApiJsonRenderer().render(schema, renderer_context={})

    reference_filename = os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))), reference_filename
    )

    with open(reference_filename.replace('.yml', '_out.yml'), 'wb') as fh:
        fh.write(schema_yml)

    if not os.path.exists(reference_filename):
        raise RuntimeError(
            f'{reference_filename} was not found for comparison. carefully inspect '
            f'the generated {reference_filename.replace(".yml", "_out.yml")} and '
            f'copy it to {reference_filename} to serve as new ground truth.'
        )

    generated = schema_yml.decode()

    with open(reference_filename) as fh:
        expected = fh.read()

    # apply optional transformations to generated result. this mainly serves to unify
    # discrepancies between Django, DRF and library versions.
    for t in transforms or []:
        generated = t(generated)

    diff = difflib.unified_diff(
        expected.splitlines(True),
        generated.splitlines(True),
    )
    diff = ''.join(diff)
    assert expected == generated and not diff, diff

    # this is more a less a sanity check as checked-in schemas should be valid anyhow
    validate_schema(schema)


def generate_schema(route, viewset=None, view=None, view_function=None):
    from django.urls import path
    from rest_framework import routers
    from rest_framework.viewsets import ViewSetMixin

    from drf_spectacular.generators import SchemaGenerator

    patterns = []
    if viewset:
        assert issubclass(viewset, ViewSetMixin)
        router = routers.SimpleRouter()
        router.register(route, viewset, basename=route)
        patterns = router.urls
    elif view:
        patterns = [path(route, view.as_view())]
    elif view_function:
        patterns = [path(route, view_function)]

    generator = SchemaGenerator(patterns=patterns)
    schema = generator.get_schema(request=None, public=True)
    validate_schema(schema)  # make sure generated schemas are always valid
    return schema


def get_response_schema(operation, status=None, content_type='application/json'):
    if (
        not status
        and operation['operationId'].endswith('_create')
        and '201' in operation['responses']
        and '200' not in operation['responses']
    ):
        status = '201'
    elif not status:
        status = '200'
    return operation['responses'][status]['content'][content_type]['schema']


def get_request_schema(operation, content_type='application/json'):
    return operation['requestBody']['content'][content_type]['schema']
