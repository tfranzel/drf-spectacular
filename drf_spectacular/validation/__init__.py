import json
import os

import jsonschema

JSON_SCHEMA_SPEC_PATH = os.path.join(os.path.dirname(__file__), 'openapi3_schema.json')


def validate_schema(api_schema):
    """
    Validate generated API schema against OpenAPI 3.0.X json schema specification.
    Note: On conflict, the written specification always wins over the json schema.

    OpenApi3 schema specification taken from:
    https://github.com/OAI/OpenAPI-Specification/blob/master/schemas/v3.0/schema.json
    https://github.com/OAI/OpenAPI-Specification/blob/6d17b631fff35186c495b9e7d340222e19d60a71/schemas/v3.0/schema.json
    """
    with open(JSON_SCHEMA_SPEC_PATH) as fh:
        openapi3_schema_spec = json.load(fh)

    # coerce any remnants of objects to basic types
    from drf_spectacular.renderers import OpenApiJsonRenderer
    api_schema = json.loads(OpenApiJsonRenderer().render(api_schema))

    jsonschema.validate(instance=api_schema, schema=openapi3_schema_spec)
