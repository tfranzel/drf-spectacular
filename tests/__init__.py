from drf_spectacular.validation import validate_schema


def assert_schema(schema, reference_file):
    from drf_spectacular.renderers import OpenApiJsonRenderer, OpenApiYamlRenderer

    schema_yml = OpenApiYamlRenderer().render(schema, renderer_context={})
    # render also a json and provoke serialization issues
    OpenApiJsonRenderer().render(schema, renderer_context={})

    with open(reference_file.replace('.yml', '_out.yml'), 'wb') as fh:
        fh.write(schema_yml)

    with open(reference_file) as fh:
        assert schema_yml.decode() == fh.read()

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
