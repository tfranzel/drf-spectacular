import re


def camelize_serializer_fields(result, generator, request, public):
    from djangorestframework_camel_case.util import camelize_re, underscore_to_camel

    def camelize_str(str):
        return re.sub(camelize_re, underscore_to_camel, str)

    def camelize_component(schema: dict):
        if schema.get('type') == 'object':
            if 'properties' in schema:
                schema['properties'] = {
                    camelize_str(field_name): camelize_component(field_schema)
                    for field_name, field_schema in schema['properties'].items()
                }
            if 'required' in schema:
                schema['required'] = [camelize_str(field) for field in schema['required']]
        elif schema.get('type') == 'array':
            camelize_component(schema['items'])
        return schema

    for (_, component_type), component in generator.registry._components.items():
        if component_type == 'schemas':
            camelize_component(component.schema)

    # inplace modification of components also affect result dict, so regeneration is not necessary
    return result
