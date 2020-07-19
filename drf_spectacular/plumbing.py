import hashlib
import inspect
import json
import sys
from abc import ABCMeta
from collections import OrderedDict, defaultdict
from collections.abc import Hashable, Iterable
from decimal import Decimal
from enum import Enum
from typing import DefaultDict, Generic, List, Optional, Type, TypeVar, Union

import uritemplate
from django import __version__ as DJANGO_VERSION
from django.apps import apps
from django.urls.resolvers import _PATH_PARAMETER_COMPONENT_RE, get_resolver  # type: ignore
from django.utils.functional import Promise
from django.utils.module_loading import import_string
from rest_framework import exceptions, fields, mixins, serializers, versioning
from uritemplate import URITemplate

from drf_spectacular.settings import spectacular_settings
from drf_spectacular.types import (
    DJANGO_PATH_CONVERTER_MAPPING, OPENAPI_TYPE_MAPPING, PYTHON_TYPE_MAPPING, OpenApiTypes,
)
from drf_spectacular.utils import OpenApiParameter

try:
    from django.db.models.enums import Choices  # only available in Django>3
except ImportError:
    class Choices:  # type: ignore
        pass

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


def get_override(obj, prop, default=None):
    if not has_override(obj, prop):
        return default
    return obj._spectacular_annotation[prop]


def get_lib_doc_excludes():
    # do not import on package level due to potential import recursion when loading
    # extensions as recommended:  USER's settings.py -> USER EXTENSIONS -> extensions.py
    # -> plumbing.py -> DRF views -> DRF DefaultSchema -> openapi.py - plumbing.py -> Loop
    from rest_framework import generics, views, viewsets
    return [
        views.APIView,
        *[getattr(serializers, c) for c in dir(serializers) if c.endswith('Serializer')],
        *[getattr(viewsets, c) for c in dir(viewsets) if c.endswith('ViewSet')],
        *[getattr(generics, c) for c in dir(generics) if c.endswith('APIView')],
        *[getattr(mixins, c) for c in dir(mixins) if c.endswith('Mixin')],
    ]


def get_doc(obj):
    """ get doc string with fallback on obj's base classes (ignoring DRF documentation). """
    if not inspect.isclass(obj):
        return inspect.getdoc(obj) or ''

    def safe_index(lst, item):
        try:
            return lst.index(item)
        except ValueError:
            return float("inf")

    lib_barrier = min(
        safe_index(obj.__mro__, c) for c in spectacular_settings.GET_LIB_DOC_EXCLUDES()
    )
    for cls in obj.__mro__[:lib_barrier]:
        if cls.__doc__:
            return inspect.cleandoc(cls.__doc__)
    return ''


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


def build_object_type(
        properties=None,
        required=None,
        description=None,
        **kwargs
):
    schema = {'type': 'object'}
    if description:
        schema['description'] = description.strip()
    if properties:
        schema['properties'] = properties
    if 'additionalParameters' in kwargs:
        schema['additionalParameters'] = kwargs.pop('additionalParameters')
    if required:
        schema['required'] = sorted(required)
    schema.update(kwargs)
    return schema


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
    if enum:
        schema['schema']['enum'] = sorted(enum)
    return schema


def build_choice_field(choices):
    choices = list(OrderedDict.fromkeys(choices))  # preserve order and remove duplicates
    if all(isinstance(choice, bool) for choice in choices):
        type = 'boolean'
    elif all(isinstance(choice, int) for choice in choices):
        type = 'integer'
    elif all(isinstance(choice, (int, float, Decimal)) for choice in choices):  # `number` includes `integer`
        # Ref: https://tools.ietf.org/html/draft-wright-json-schema-validation-00#section-5.21
        type = 'number'
    elif all(isinstance(choice, str) for choice in choices):
        type = 'string'
    else:
        type = None

    schema = {
        # The value of `enum` keyword MUST be an array and SHOULD be unique.
        # Ref: https://tools.ietf.org/html/draft-wright-json-schema-validation-00#section-5.20
        'enum': choices
    }

    # If We figured out `type` then and only then we should set it. It must be a string.
    # Ref: https://swagger.io/docs/specification/data-models/data-types/#mixed-type
    # It is optional but it can not be null.
    # Ref: https://tools.ietf.org/html/draft-wright-json-schema-validation-00#section-5.21
    if type:
        schema['type'] = type
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
        elif callable(field_or_property):
            return field_or_property
        else:
            return get_field_from_model(model, field_or_property)
    else:
        if isinstance(field_or_property, property) or callable(field_or_property):
            if isinstance(field_or_property, property):
                target_model = field_or_property.fget.__annotations__.get('return')
            else:
                target_model = field_or_property.__annotations__.get('return')
            if not target_model:
                raise UnableToProceedError(
                    f'could not follow field source through intermediate property "{path[0]}" '
                    f'on model {model}. please add a type hint on the model\'s property/function'
                    f'to enable traversal of the source path "{".".join(path)}".'
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
    except Exception as exc:
        warn(
            f'could not resolve field on model {model} with path "{".".join(path)}". '
            f'this is likely a custom field that does some unknown magic. maybe '
            f'consider annotating the field/property? defaulting to "string". (Exception: {exc})'
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

    # Sort foo{arg} after foo/, but before foo/bar
    if path.endswith('/'):
        path = path[:-1] + ' '
    path = path.replace('{', '!')

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
        return bool(self.name and self.type and self.object)

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
        if component.key in self._components:
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
            installed_apps = apps.app_configs.keys()
            if any(cls.target_class.startswith(app + '.') for app in installed_apps):
                warn(
                    f'registered extensions {cls.__name__} for "{cls.target_class}" '
                    f'has an installed app but target class was not found.'
                )
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


def deep_import_string(string):
    """ augmented import from string, e.g. MODULE.CLASS/OBJECT.ATTRIBUTE """
    try:
        return import_string(string)
    except ImportError:
        pass
    try:
        *path, attr = string.split('.')
        obj = import_string('.'.join(path))
        return getattr(obj, attr)
    except (ImportError, AttributeError):
        pass


def load_enum_name_overrides():
    overrides = {}
    for name, choices in spectacular_settings.ENUM_NAME_OVERRIDES.items():
        if isinstance(choices, str):
            choices = deep_import_string(choices)
        if not choices:
            warn(
                f'unable to load choice override for {name} from ENUM_NAME_OVERRIDES. '
                f'please check module path string.'
            )
            continue
        if inspect.isclass(choices) and issubclass(choices, Choices):
            choices = choices.choices
        if inspect.isclass(choices) and issubclass(choices, Enum):
            choices = [c.value for c in choices]
        if isinstance(choices, Iterable) and isinstance(choices[0], str):
            choices = [(c, c) for c in choices]
        overrides[list_hash(list(dict(choices).keys()))] = name

    if len(spectacular_settings.ENUM_NAME_OVERRIDES) != len(overrides):
        error(
            'ENUM_NAME_OVERRIDES has duplication issues. encountered multiple names '
            'for the same choice set. enum naming might be unexpected.'
        )
    return overrides


def list_hash(lst):
    return hashlib.blake2b(json.dumps(list(lst), sort_keys=True).encode()).hexdigest()


def resolve_regex_path_parameter(path_regex, variable, available_formats):
    """
    convert django style path parameters to OpenAPI parameters.
    TODO also try to handle regular grouped regex parameters
    """
    for match in _PATH_PARAMETER_COMPONENT_RE.finditer(path_regex):
        converter, parameter = match.group('converter'), match.group('parameter')
        enum_values = None

        if converter and converter.startswith('drf_format_suffix_'):
            explicit_formats = converter[len('drf_format_suffix_'):].split('_')
            enum_values = [
                f'.{suffix}' for suffix in explicit_formats if suffix in available_formats
            ]
            converter = 'drf_format_suffix'
        elif converter == 'drf_format_suffix':
            enum_values = [f'.{suffix}' for suffix in available_formats]

        if parameter == variable and converter in DJANGO_PATH_CONVERTER_MAPPING:
            return build_parameter_type(
                name=parameter,
                schema=build_basic_type(DJANGO_PATH_CONVERTER_MAPPING[converter]),
                location=OpenApiParameter.PATH,
                enum=enum_values,
            )

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
        path = uritemplate.partial(path, var_dict={version_param: requested_version})
        if isinstance(path, URITemplate):
            path = path.uri
        # emulate router behaviour by injecting substituted variable into view
        view.kwargs[version_param] = requested_version
    elif issubclass(view.versioning_class, versioning.NamespaceVersioning):
        mocked_request.resolver_match = get_resolver(tuple(patterns)).resolve(path)

    return path


def normalize_result_object(result):
    """ resolve non-serializable objects like lazy translation strings and OrderedDict """
    if isinstance(result, dict) or isinstance(result, OrderedDict):
        return {k: normalize_result_object(v) for k, v in result.items()}
    if isinstance(result, list) or isinstance(result, tuple):
        return [normalize_result_object(v) for v in result]
    if isinstance(result, Promise):
        return str(result)
    return result
