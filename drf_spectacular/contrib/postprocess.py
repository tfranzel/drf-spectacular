import re


def camelize_serializer_fields(result, generator, request, public):
    from djangorestframework_camel_case.util import camelize, camelize_re, underscore_to_camel

    for component in generator.registry._components.values():
        if 'properties' in component.schema:
            component.schema['properties'] = camelize(component.schema['properties'])
        if 'required' in component.schema:
            component.schema['required'] = [
                re.sub(camelize_re, underscore_to_camel, key) for key in component.schema['required']
            ]

    # inplace modification of components also affect result dict, so regeneration is not necessary
    return result
