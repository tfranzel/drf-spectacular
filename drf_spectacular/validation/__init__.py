import json
import os

import yaml

try:
    import jsonschema
except ImportError:
    jsonschema = None


JSON_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'openapi3_schema.json')


def validate_schema(api_schema):
    """
    Validate generated API schema against OpenAPI 3.0.X json schema specification.
    Note: On conflict, the written specification always wins over the json schema.

    OpenApi3 schema specification taken from:
    https://github.com/OAI/OpenAPI-Specification/blob/master/schemas/v3.0/schema.json
    https://github.com/OAI/OpenAPI-Specification/blob/6d17b631fff35186c495b9e7d340222e19d60a71/schemas/v3.0/schema.json
    """
    with open(JSON_SCHEMA_PATH) as fh:
        openapi3_schema_spec = json.load(fh)

    if isinstance(api_schema, str):
        with open(api_schema) as fh:
            if api_schema.lower().endswith('.json'):
                api_schema = json.load(fh)
            elif api_schema.lower().endswith('.yml') or api_schema.lower().endswith('.yml'):
                api_schema = yaml.load(fh, Loader=yaml.SafeLoader)
            else:
                raise ValueError(
                    'API schema must be either an python object or a path string '
                    'with file ending in .json .yml or .yaml'
                )
    else:
        # pass
        api_schema = json.loads(json.dumps(api_schema))

    jsonschema.validate(instance=api_schema, schema=openapi3_schema_spec)
