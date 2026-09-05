import json
import os

import jsonschema

#: Keywords that exist in JSON Schema drafts but are not part of the Schema Object
#: of the given OpenAPI version. Validation rejects the whole enclosing object via
#: the Schema/Reference ``oneOf``, which never names the keyword that caused it.
OPENAPI_UNSUPPORTED_KEYWORDS = {
    '3.0': frozenset({
        'propertyNames', 'const', 'prefixItems', 'if', 'then', 'else',
        'dependentSchemas', 'dependentRequired', 'contains', 'patternProperties',
        'unevaluatedItems', 'unevaluatedProperties', '$defs',
    }),
    '3.1': frozenset(),
    '3.2': frozenset(),
}


def validate_schema(api_schema):
    """
    Validate generated API schema against OpenAPI 3.0.X json schema specification.
    Note: On conflict, the written specification always wins over the json schema.

    OpenApi3 schema specification taken from:

    https://github.com/OAI/OpenAPI-Specification/blob/master/schemas/v3.0/schema.json
    https://github.com/OAI/OpenAPI-Specification/blob/9dff244e5708fbe16e768738f4f17cf3fddf4066/schemas/v3.0/schema.json

    https://github.com/OAI/OpenAPI-Specification/blob/main/schemas/v3.1/schema.json
    https://github.com/OAI/OpenAPI-Specification/blob/9dff244e5708fbe16e768738f4f17cf3fddf4066/schemas/v3.1/schema.json
    """
    if api_schema['openapi'].startswith("3.0"):
        version = '3.0'
        schema_spec_path = os.path.join(os.path.dirname(__file__), 'openapi_3_0_schema.json')
    elif api_schema['openapi'].startswith("3.1"):
        version = '3.1'
        schema_spec_path = os.path.join(os.path.dirname(__file__), 'openapi_3_1_schema.json')
    elif api_schema['openapi'].startswith("3.2"):
        version = '3.2'
        schema_spec_path = os.path.join(os.path.dirname(__file__), 'openapi_3_2_schema.json')
    else:
        raise RuntimeError('No validation specification available')  # pragma: no cover

    with open(schema_spec_path) as fh:
        openapi3_schema_spec = json.load(fh)

    # coerce any remnants of objects to basic types
    from drf_spectacular.renderers import OpenApiJsonRenderer
    api_schema = json.loads(OpenApiJsonRenderer().render(api_schema))

    try:
        jsonschema.validate(instance=api_schema, schema=openapi3_schema_spec)
    except jsonschema.exceptions.ValidationError as exc:
        hint = _unsupported_keyword_hint(exc, version)
        if hint:
            # Re-raise with the keyword named. The original error points at the
            # Schema/Reference ``oneOf`` and dumps the whole object, which reads as a
            # problem with whichever sibling key the user happens to look at first.
            raise jsonschema.exceptions.ValidationError(f'{exc.message}\n\n{hint}') from exc
        raise


#: Mappings whose *keys* are user-chosen names rather than schema keywords. A field
#: legitimately named "const" must not be mistaken for the ``const`` keyword.
_NAME_KEYED_SUBSCHEMAS = ('properties', 'patternProperties', 'definitions', '$defs')


def _find_unsupported_keywords(node, unsupported):
    """Collect keywords in ``node`` that the target OpenAPI version does not define."""
    found = set()
    if isinstance(node, dict):
        found |= unsupported.intersection(node)
        for key, value in node.items():
            if key in _NAME_KEYED_SUBSCHEMAS and isinstance(value, dict):
                # Recurse into the sub-schemas, but do not read their keys as keywords.
                for sub_schema in value.values():
                    found |= _find_unsupported_keywords(sub_schema, unsupported)
            else:
                found |= _find_unsupported_keywords(value, unsupported)
    elif isinstance(node, list):
        for value in node:
            found |= _find_unsupported_keywords(value, unsupported)
    return found


def _unsupported_keyword_hint(exc, version):
    """Return a hint naming JSON Schema keywords illegal in this OpenAPI version, if any."""
    unsupported = OPENAPI_UNSUPPORTED_KEYWORDS.get(version)
    if not unsupported:
        return None
    found = _find_unsupported_keywords(exc.instance, unsupported)
    if not found:
        return None
    location = '/'.join(str(part) for part in exc.absolute_path)
    names = ', '.join(repr(name) for name in sorted(found))
    hint = (
        f'Hint: {names} at #/{location} '
        f'{"is a JSON Schema keyword" if len(found) == 1 else "are JSON Schema keywords"} '
        f'not present in the OpenAPI {version} Schema Object.'
    )
    if 'propertyNames' in found:
        hint += (
            ' To constrain object keys, spell each key out under "properties" and set'
            ' "additionalProperties": False.'
        )
    return hint
