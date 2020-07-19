from collections import defaultdict

import inflection
from rest_framework.settings import api_settings

from drf_spectacular.plumbing import (
    ResolvedComponent, list_hash, load_enum_name_overrides, safe_ref, warn,
)
from drf_spectacular.settings import spectacular_settings


def postprocess_schema_enums(result, generator, **kwargs):
    """
    simple replacement of Enum/Choices that globally share the same name and have
    the same choices. Aids client generation to not generate a separate enum for
    every occurrence. only takes effect when replacement is guaranteed to be correct.
    """

    def iter_prop_containers(schema):
        if isinstance(schema, list):
            for item in schema:
                yield from iter_prop_containers(item)
        elif isinstance(schema, dict):
            if schema.get('properties'):
                yield schema['properties']
            yield from iter_prop_containers(schema.get('oneOf', []))
            yield from iter_prop_containers(schema.get('allOf', []))

    schemas = result.get('components', {}).get('schemas', {})

    overrides = load_enum_name_overrides()

    hash_mapping = defaultdict(set)
    # collect all enums, their names and choice sets
    for props in iter_prop_containers(list(schemas.values())):
        for prop_name, prop_schema in props.items():
            if 'enum' not in prop_schema:
                continue
            hash_mapping[prop_name].add(list_hash(prop_schema['enum']))

    # traverse all enum properties and generate a name for the choice set. naming collisions
    # are resolved and a warning is emitted. giving a choice set multiple names is technically
    # correct but potentially unwanted. also emit a warning there to make the user aware.
    enum_name_mapping = {}
    for prop_name, prop_hash_set in hash_mapping.items():
        for prop_hash in prop_hash_set:
            if prop_hash in overrides:
                enum_name = overrides[prop_hash]
            elif len(prop_hash_set) == 1:
                enum_name = f'{inflection.camelize(prop_name)}Enum'
            else:
                enum_name = f'{inflection.camelize(prop_name)}{prop_hash[:3].capitalize()}Enum'
                warn(
                    f'automatic enum naming encountered a collision for field "{prop_name}". the '
                    f'same name has been used for multiple choice sets. the collision was resolved '
                    f'with {enum_name}. add an entry to ENUM_NAME_OVERRIDES to fix the naming.'
                )
            if enum_name_mapping.get(prop_hash, enum_name) != enum_name:
                warn(
                    f'encountered multiple names for the same choice set ({enum_name}). this '
                    f'may be unwanted even though the generated schema is technically correct. '
                    f'add an entry to ENUM_NAME_OVERRIDES to fix the naming.'
                )
                del enum_name_mapping[prop_hash]
            else:
                enum_name_mapping[prop_hash] = enum_name
            enum_name_mapping[(prop_hash, prop_name)] = enum_name

    # replace all enum occurrences with a enum schema component. cut out the
    # enum, replace it with a reference and add a corresponding component.
    for props in iter_prop_containers(list(schemas.values())):
        for prop_name, prop_schema in props.items():
            if 'enum' not in prop_schema:
                continue

            prop_hash = list_hash(prop_schema['enum'])
            # when choice sets are reused under multiple names, the generated name cannot be
            # resolved from the hash alone. fall back to prop_name and hash for resolution.
            enum_name = enum_name_mapping.get(prop_hash) or enum_name_mapping[prop_hash, prop_name]

            enum_schema = {k: v for k, v in prop_schema.items() if k in ['type', 'enum']}
            prop_schema = {k: v for k, v in prop_schema.items() if k not in ['type', 'enum']}

            component = ResolvedComponent(
                name=enum_name,
                type=ResolvedComponent.SCHEMA,
                schema=enum_schema,
                object=enum_name,
            )
            if component not in generator.registry:
                generator.registry.register(component)
            prop_schema.update(component.ref)
            props[prop_name] = safe_ref(prop_schema)

    # sort again with additional components
    result['components'] = generator.registry.build(spectacular_settings.APPEND_COMPONENTS)
    return result


def preprocess_exclude_path_format(endpoints, **kwargs):
    """
        preprocessing hook that filters out {format} suffixed paths, in case
        format_suffix_patterns is used and {format} path params are unwanted.
    """
    format_path = f'{{{api_settings.FORMAT_SUFFIX_KWARG}}}'
    return [
        (path, path_regex, method, callback) for path, path_regex, method, callback in endpoints
        if not (path.endswith(format_path) or path.endswith(format_path + '/'))
    ]
