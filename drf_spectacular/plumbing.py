import inspect
import json
import sys
from abc import ABCMeta
from collections import defaultdict
from collections.abc import Hashable
from typing import List, Type, Optional, TypeVar, Union, Generic, DefaultDict

import inflection
import uritemplate
from django import __version__ as DJANGO_VERSION
from django.urls.resolvers import _PATH_PARAMETER_COMPONENT_RE, get_resolver  # type: ignore
from django.utils.module_loading import import_string
from rest_framework import fields, serializers, versioning, exceptions

from drf_spectacular.settings import spectacular_settings
from drf_spectacular.types import (
    OPENAPI_TYPE_MAPPING, PYTHON_TYPE_MAPPING, DJANGO_PATH_CONVERTER_MAPPING, OpenApiTypes
)
from drf_spectacular.utils import OpenApiParameter

T = TypeVar('T')


class UnableToProceedError(Exception):
    pass


class GeneratorStats:
    _warn_cache: DefaultDict[str, int] = defaultdict(int)
    _error_cache: DefaultDict[str, int] = defaultdict(int)

    def __bool__(self):
        return bool(self._warn_cache or self._error_cache)

    def reset(self):
        self._warn_cache.clear()
        self._error_cache.clear()

    def emit(self, msg, severity):
        assert severity in ['warning', 'error']
        msg = str(msg)
        cache = self._warn_cache if severity == 'warning' else self._error_cache
        if msg not in cache:
            print(f'{severity.capitalize()} #{len(cache)}: {msg}', file=sys.stderr)
        cache[msg] += 1

    def emit_summary(self):
        if self._warn_cache or self._error_cache:
            print(
                f'\nSchema generation summary:\n'
                f'Warnings: {sum(self._warn_cache.values())} ({len(self._warn_cache)} unique)\n'
                f'Errors:   {sum(self._error_cache.values())} ({len(self._error_cache)} unique)\n',
                file=sys.stderr
            )


GENERATOR_STATS = GeneratorStats()


def warn(msg):
    GENERATOR_STATS.emit(msg, 'warning')


def error(msg):
    GENERATOR_STATS.emit(msg, 'error')


def reset_generator_stats():
    GENERATOR_STATS.reset()


def anyisinstance(obj, type_list):
    return any([isinstance(obj, t) for t in type_list])


def get_class(obj) -> type:
    return obj if inspect.isclass(obj) else obj.__class__


def force_instance(serializer_or_field):
    if not inspect.isclass(serializer_or_field):
        return serializer_or_field
    elif issubclass(serializer_or_field, (serializers.BaseSerializer, fields.Field)):
        return serializer_or_field()
    else:
        return serializer_or_field


def is_serializer(obj) -> bool:
    from drf_spectacular.serializers import OpenApiSerializerExtension
    return (
        isinstance(force_instance(obj), serializers.BaseSerializer)
        or bool(OpenApiSerializerExtension.get_match(obj))
    )


def is_field(obj):
    # make sure obj is a serializer field and nothing else.
    # guard against serializers because BaseSerializer(Field)
    return isinstance(force_instance(obj), fields.Field) and not is_serializer(obj)


def is_basic_type(obj):
    if not isinstance(obj, Hashable):
        return False
    return obj in OPENAPI_TYPE_MAPPING or obj in PYTHON_TYPE_MAPPING


def has_override(obj, prop):
    if not hasattr(obj, '_spectacular_annotation'):
        return False
    if prop not in obj._spectacular_annotation:
        return False
    return True


def get_override(obj, prop):
    if not has_override(obj, prop):
        return None
    return obj._spectacular_annotation[prop]


def build_basic_type(obj):
    """
    resolve either enum or actual type and yield schema template for modification
    """
    if obj in OPENAPI_TYPE_MAPPING:
        return dict(OPENAPI_TYPE_MAPPING[obj])
    elif obj in PYTHON_TYPE_MAPPING:
        return dict(OPENAPI_TYPE_MAPPING[PYTHON_TYPE_MAPPING[obj]])
    elif obj is None or type(obj) is None:
        return dict(OPENAPI_TYPE_MAPPING[OpenApiTypes.NONE])
    else:
        warn(f'could not resolve type for "{obj}". defaulting to "string"')
        return dict(OPENAPI_TYPE_MAPPING[OpenApiTypes.STR])


def build_array_type(schema):
    return {
        'type': 'array',
        'items': schema,
    }


def build_parameter_type(
        name,
        schema,
        location,
        required=False,
        description=None,
        enum=None,
        deprecated=False,
        explode=None,
        style=None
):
    schema = {
        'in': location,
        'name': name,
        'schema': schema,
    }
    if description:
        schema['description'] = description
    if required or location == 'path':
        schema['required'] = True
    if deprecated:
        schema['deprecated'] = True
    if explode is not None:
        schema['explode'] = explode
    if style is not None:
        schema['style'] = style
    if enum is not None:
        schema['schema']['enum'] = enum
    return schema


def build_root_object(paths, components):
    settings = spectacular_settings
    root = {
        'openapi': '3.0.3',
        'info': {
            'title': settings.TITLE,
            'version': settings.VERSION,
        },
        'paths': {**paths, **settings.APPEND_PATHS},
        'components': components
    }
    if settings.DESCRIPTION:
        root['info']['description'] = settings.DESCRIPTION
    if settings.TOS:
        root['info']['termsOfService'] = settings.TOS
    if settings.CONTACT:
        root['info']['contact'] = settings.CONTACT
    if settings.LICENSE:
        root['info']['license'] = settings.LICENSE
    if settings.SERVERS:
        root['servers'] = settings.SERVERS
    if settings.SECURITY:
        root['security'] = settings.SECURITY
    if settings.TAGS:
        root['tags'] = settings.TAGS
    if settings.EXTERNAL_DOCS:
        root['externalDocs'] = settings.EXTERNAL_DOCS
    return root


def safe_ref(schema):
    """
    ensure that $ref has its own context and does not remove potential sibling
    entries when $ref is substituted.
    """
    if '$ref' in schema and len(schema) > 1:
        return {'allOf': [{'$ref': schema.pop('$ref')}], **schema}
    return schema


def append_meta(schema, meta):
    return safe_ref({**schema, **meta})


def get_field_from_model(model, field):
    """
    this is a Django 2.2 compatibility function to access a field through a Deferred Attribute
    """
    if DJANGO_VERSION.startswith('2'):
        # field.field will in effect return self, i.e. a DeferredAttribute again (loop)
        return model._meta.get_field(field.field_name)
    else:
        return field.field


def _follow_field_source(model, path):
    field_or_property = getattr(model, path[0])

    if len(path) == 1:
        # end of traversal
        if isinstance(field_or_property, property):
            return field_or_property.fget
        else:
            return get_field_from_model(model, field_or_property)
    else:
        if isinstance(field_or_property, property):
            target_model = field_or_property.fget.__annotations__.get('return')
            if not target_model:
                raise UnableToProceedError(
                    f'could not follow field source through intermediate property "{path[0]}" '
                    f'on model {model}. please add a type hint on the model\'s property to '
                    f'enable traversal of the source path "{".".join(path)}".'
                )
            return _follow_field_source(target_model, path[1:])
        else:
            target_model = field_or_property.field.related_model
            return _follow_field_source(target_model, path[1:])


def follow_field_source(model, path):
    """
    a model traversal chain "foreignkey.foreignkey.value" can either end with an actual model field
    instance "value" or a model property function named "value". differentiate the cases.

    :return: models.Field or function object
    """
    try:
        return _follow_field_source(model, path)
    except UnableToProceedError as e:
        warn(e)
    except:  # noqa: E722
        warn(
            f'could not resolve field on model {model} with path "{".".join(path)}". '
            f'this is likely a custom field that does some unknown magic. maybe '
            f'consider annotating the field/property? defaulting to "string".'
        )

    def dummy_property(obj) -> str:
        pass
    return dummy_property


def alpha_operation_sorter(endpoint):
    """ sort endpoints first alphanumerically by path, then by method order """
    path, path_regex, method, callback = endpoint
    method_priority = {
        'GET': 0,
        'POST': 1,
        'PUT': 2,
        'PATCH': 3,
        'DELETE': 4
    }.get(method, 5)
    return path, method_priority


class ResolvedComponent:
    SCHEMA = 'schemas'
    SECURITY_SCHEMA = 'securitySchemes'

    def __init__(self, name, type, schema=None, object=None):
        self.name = name
        self.type = type
        self.schema = schema
        self.object = object

    def __bool__(self):
        return bool(self.schema)

    @property
    def key(self):
        return self.name, self.type

    @property
    def ref(self) -> dict:
        assert self.name and self.type and self.object
        return {'$ref': f'#/components/{self.type}/{self.name}'}


class ComponentRegistry:
    def __init__(self):
        self._components = {}

    def register(self, component: ResolvedComponent):
        if self._components.get(component.key, None):
            warn(
                f'trying to re-register a {component.type} component with name '
                f'{self._components[component.key].name}. this might lead to '
                f'a incorrect schema. Look out for reused names'
            )
        self._components[component.key] = component

    def __contains__(self, component):
        if component.key not in self._components:
            return False

        query_obj = component.object
        registry_obj = self._components[component.key].object
        query_class = query_obj if inspect.isclass(query_obj) else query_obj.__class__
        registry_class = query_obj if inspect.isclass(registry_obj) else registry_obj.__class__

        if query_class != registry_class:
            warn(
                f'Encountered 2 components with identical names "{component.name}" and '
                f'different classes {query_class} and {registry_class}. This will very '
                f'likely result in an incorrect schema. Try renaming one.'
            )
        return True

    def __getitem__(self, key):
        if isinstance(key, ResolvedComponent):
            key = key.key
        return self._components[key]

    def __delitem__(self, key):
        if isinstance(key, ResolvedComponent):
            key = key.key
        del self._components[key]

    def build(self, extra_components) -> dict:
        output: DefaultDict[str, dict] = defaultdict(dict)
        # build tree from flat registry
        for component in self._components.values():
            output[component.type][component.name] = component.schema
        # add/override extra components
        for extra_type, extra_component_dict in extra_components.items():
            for component_name, component_schema in extra_component_dict.items():
                output[extra_type][component_name] = component_schema
        # sort by component type then by name
        return {
            type: {name: output[type][name] for name in sorted(output[type].keys())}
            for type in sorted(output.keys())
        }


class OpenApiGeneratorExtension(Generic[T], metaclass=ABCMeta):
    _registry: List[T] = []
    target_class: Union[None, str, Type[object]] = None
    match_subclasses = False
    priority = 0

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._registry.append(cls)

    def __init__(self, target):
        self.target = target

    @classmethod
    def _load_class(cls):
        try:
            cls.target_class = import_string(cls.target_class)
        except ImportError:
            cls.target_class = None

    @classmethod
    def _matches(cls, target) -> bool:
        if isinstance(cls.target_class, str):
            cls._load_class()

        if cls.target_class is None:
            return False  # app not installed
        elif cls.match_subclasses:
            return issubclass(get_class(target), cls.target_class)  # type: ignore
        else:
            return get_class(target) == cls.target_class

    @classmethod
    def get_match(cls, target) -> Optional[T]:
        for extension in sorted(cls._registry, key=lambda e: e.priority, reverse=True):
            if extension._matches(target):
                return extension(target)
        return None


def postprocess_schema_enums(result, **kwargs):
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

    # schemas will be modified in-place and same result object is returned
    schemas = result.get('components', {}).get('schemas', {})

    hash_mapping = defaultdict(set)
    # collect all enums, their names and contents
    for props in iter_prop_containers(list(schemas.values())):
        for prop_name, prop_schema in props.items():
            if 'enum' not in prop_schema:
                continue
            hash_mapping[prop_name].add(
                hash(json.dumps(prop_schema['enum'], sort_keys=True))
            )
    # safe replacement requires name to have only one set of enum values
    candidate_enums = {
        prop_name for prop_name, prop_hash_set in hash_mapping.items()
        if len(prop_hash_set) == 1
    }
    # replace all valid occurrences with enum schema component
    for props in iter_prop_containers(list(schemas.values())):
        for prop_name, prop_schema in props.items():
            if 'enum' not in prop_schema:
                continue
            if prop_name not in candidate_enums:
                continue

            enum_name = f'{inflection.camelize(prop_name)}Enum'
            enum_schema = {k: v for k, v in prop_schema.items() if k in ['type', 'enum']}
            prop_schema = {k: v for k, v in prop_schema.items() if k not in ['type', 'enum']}
            prop_schema['$ref'] = f'#/components/schemas/{enum_name}'

            schemas[enum_name] = enum_schema
            props[prop_name] = safe_ref(prop_schema)

    return result


def resolve_regex_path_parameter(path_regex, variable):
    """
    convert django style path parameters to OpenAPI parameters.
    TODO also try to handle regular grouped regex parameters
    """
    for match in _PATH_PARAMETER_COMPONENT_RE.finditer(path_regex):
        converter, parameter = match.group('converter'), match.group('parameter')

        if converter and converter.startswith('drf_format_suffix_'):
            converter = 'drf_format_suffix'  # remove appended options

        if parameter == variable and converter in DJANGO_PATH_CONVERTER_MAPPING:
            return {
                'name': parameter,
                'schema': build_basic_type(DJANGO_PATH_CONVERTER_MAPPING[converter]),
                'in': OpenApiParameter.PATH,
                'required': False if converter == 'drf_format_suffix' else True,
            }

    return None


def is_versioning_supported(versioning_class):
    return bool(
        issubclass(versioning_class, versioning.URLPathVersioning)
        or issubclass(versioning_class, versioning.NamespaceVersioning)
    )


def operation_matches_version(view, requested_version):
    try:
        version, _ = view.determine_version(view.request, **view.kwargs)
    except exceptions.NotAcceptable:
        return False
    else:
        return str(version) == str(requested_version)


def modify_for_versioning(patterns, method, path, view, requested_version):
    assert view.versioning_class

    from rest_framework.test import APIRequestFactory
    mocked_request = getattr(APIRequestFactory(), method.lower())(path=path)
    view.request = mocked_request

    mocked_request.version = requested_version

    if issubclass(view.versioning_class, versioning.URLPathVersioning):
        version_param = view.versioning_class.version_param
        # substitute version variable to emulate request
        path = uritemplate.expand(path, var_dict={version_param: requested_version})
        # emulate router behaviour by injecting substituted variable into view
        view.kwargs[version_param] = requested_version
    elif issubclass(view.versioning_class, versioning.NamespaceVersioning):
        mocked_request.resolver_match = get_resolver(tuple(patterns)).resolve(path)

    return path
