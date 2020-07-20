import os
import sys

from diff_match_patch import diff_match_patch

from drf_spectacular.validation import validate_schema


def assert_schema(schema, reference_filename, transforms=None):
    from drf_spectacular.renderers import OpenApiJsonRenderer, OpenApiYamlRenderer

    schema_yml = OpenApiYamlRenderer().render(schema, renderer_context={})
    # render also a json and provoke serialization issues
    OpenApiJsonRenderer().render(schema, renderer_context={})

    if not os.path.exists(reference_filename):
        generated_filename = reference_filename
    else:
        generated_filename = reference_filename.replace('.yml', '_out.yml')

    with open(generated_filename, 'wb') as fh:
        fh.write(schema_yml)

    if generated_filename == reference_filename:
        raise RuntimeError(
            f'{reference_filename} was not found. '
            f'It has been created with the generated schema. '
            f'Review carefully, as it is the baseline for subsequent checks.')

    generated = schema_yml.decode()

    with open(reference_filename) as fh:
        expected = fh.read()

    # This only does each transform, however it may be necessary to do all
    # combinations of transforms.
    # Force to be a list, and insert identity
    if transforms:
        transforms = [lambda x: x] + list(transforms)
    else:
        transforms = [lambda x: x]

    results = []
    for result in (transformer(generated) for transformer in transforms):
        if result not in results:
            results.append(result)
            if result == expected:
                break
    else:
        dmp = diff_match_patch()
        diff = dmp.diff_main(expected, generated)
        dmp.diff_cleanupSemantic(diff)
        patch = dmp.patch_toText(dmp.patch_make(diff))
        assert patch, f'Failed to generate patch from "{expected}" to "{generated}"'
        msg = f"Patch from {reference_filename} to {generated_filename}: {patch}"
        if len(transforms) and len(results) != len(transforms):
            msg = f'{len(transforms) - 1} transformers ineffective: {msg}'
        print(msg, file=sys.stderr)
        assert expected == generated, msg

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


def get_response_schema(operation, status='200', content_type='application/json'):
    return operation['responses'][status]['content'][content_type]['schema']


def get_request_schema(operation, content_type='application/json'):
    return operation['requestBody']['content'][content_type]['schema']
