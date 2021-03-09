import hashlib
import inspect
import json
import re
import sys
import typing
import urllib.parse
from abc import ABCMeta
from collections import OrderedDict, defaultdict
from collections.abc import Hashable
from decimal import Decimal
from enum import Enum
from typing import DefaultDict, Generic, List, Optional, Type, TypeVar, Union

import inflection
import uritemplate
from django.apps import apps
from django.db.models.fields.related_descriptors import (
    ForwardManyToOneDescriptor, ManyToManyDescriptor, ReverseManyToOneDescriptor,
    ReverseOneToOneDescriptor,
)
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.urls.resolvers import (  # type: ignore
    _PATH_PARAMETER_COMPONENT_RE, RegexPattern, Resolver404, RoutePattern, URLPattern, URLResolver,
    get_resolver,
)
from django.utils.functional import Promise, cached_property
from django.utils.module_loading import import_string
from rest_framework import exceptions, fields, mixins, serializers, versioning
from rest_framework.settings import api_settings
from rest_framework.test import APIRequestFactory
from rest_framework.utils.mediatypes import _MediaType
from uritemplate import URITemplate

from drf_spectacular.drainage import error, warn
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


def is_list_serializer(obj) -> bool:
    return isinstance(force_instance(obj), serializers.ListSerializer)


def is_field(obj):
    # make sure obj is a serializer field and nothing else.
    # guard against serializers because BaseSerializer(Field)
    return isinstance(force_instance(obj), fields.Field) and not is_serializer(obj)


def is_basic_type(obj, allow_none=True):
    if not isinstance(obj, Hashable):
        return False
    if not allow_none and (obj is None or obj is OpenApiTypes.NONE):
        return False
    return obj in OPENAPI_TYPE_MAPPING or obj in PYTHON_TYPE_MAPPING


def is_patched_serializer(serializer, direction):
    return bool(
        spectacular_settings.COMPONENT_SPLIT_PATCH
        and serializer.partial
        and not serializer.read_only
        and not (spectacular_settings.COMPONENT_SPLIT_REQUEST and direction == 'response')
    )


def is_trivial_string_variation(a: str, b: str):
    a = (a or '').strip().lower().replace(' ', '_').replace('-', '_')
    b = (b or '').strip().lower().replace(' ', '_').replace('-', '_')
    return a == b


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


def get_view_model(view):
    """
    obtain model from view via view's queryset. try safer view attribute first
    before going through get_queryset(), which may perform arbitrary operations.
    """
    model = getattr(getattr(view, 'queryset', None), 'model', None)

    if model is not None:
        return model

    try:
        return view.get_queryset().model
    except Exception as exc:
        warn(
            f'failed to obtain model through view\'s queryset due to raised exception. '
            f'Prevent this either by setting "queryset = Model.objects.none()" on the view, '
            f'having an empty fallback in get_queryset() or by using @extend_schema. '
            f'(Exception: {exc})'
        )


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
            # dedent and cleanup of trailing white space on each line
            doc = inspect.cleandoc(cls.__doc__)
            doc = '\n'.join(line.rstrip() for line in doc.rstrip().split('\n'))
            return doc
    return ''


def build_basic_type(obj):
    """
    resolve either enum or actual type and yield schema template for modification
    """
    if obj is None or type(obj) is None or obj is OpenApiTypes.NONE:
        return None
    elif obj in OPENAPI_TYPE_MAPPING:
        return dict(OPENAPI_TYPE_MAPPING[obj])
    elif obj in PYTHON_TYPE_MAPPING:
        return dict(OPENAPI_TYPE_MAPPING[PYTHON_TYPE_MAPPING[obj]])
    else:
        warn(f'could not resolve type for "{obj}". defaulting to "string"')
        return dict(OPENAPI_TYPE_MAPPING[OpenApiTypes.STR])


def build_array_type(schema, min_length=None, max_length=None):
    schema = {'type': 'array', 'items': schema}
    if min_length is not None:
        schema['minLength'] = min_length
    if max_length is not None:
        schema['maxLength'] = max_length
    return schema


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
    if 'additionalProperties' in kwargs:
        schema['additionalProperties'] = kwargs.pop('additionalProperties')
    if required:
        schema['required'] = sorted(required)
    schema.update(kwargs)
    return schema


def build_media_type_object(schema, examples=None):
    media_type_object = {'schema': schema}
    if examples:
        media_type_object['examples'] = examples
    return media_type_object


def build_examples_list(examples):
    schema = {}
    for example in examples:
        normalized_name = inflection.camelize(example.name.replace(' ', '_'))
        sub_schema = {}
        if example.value:
            sub_schema['value'] = example.value
        if example.external_value:
            sub_schema['externalValue'] = example.external_value
        if example.summary:
            sub_schema['summary'] = example.summary
        elif normalized_name != example.name:
            sub_schema['summary'] = example.name
        if example.description:
            sub_schema['description'] = example.description
        schema[normalized_name] = sub_schema
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
        style=None,
        default=None,
        examples=None,
):
    irrelevant_field_meta = ['readOnly', 'writeOnly']
    if location == OpenApiParameter.PATH:
        irrelevant_field_meta += ['nullable', 'default']
    schema = {
        'in': location,
        'name': name,
        'schema': {k: v for k, v in schema.items() if k not in irrelevant_field_meta},
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
    if default is not None and 'default' not in irrelevant_field_meta:
        schema['schema']['default'] = default
    if examples:
        schema['examples'] = examples
    return schema


def build_choice_field(field):
    choices = list(OrderedDict.fromkeys(field.choices))  # preserve order and remove duplicates

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

    if field.allow_blank:
        choices.append('')
    if field.allow_null:
        choices.append(None)

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


def build_root_object(paths, components, version):
    settings = spectacular_settings
    if settings.VERSION and version:
        version = f'{settings.VERSION} ({version})'
    else:
        version = settings.VERSION or version or ''
    root = {
        'openapi': '3.0.3',
        'info': {
            'title': settings.TITLE,
            'version': version,
            **settings.EXTENSIONS_INFO,
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


def _follow_field_source(model, path: List[str]):
    """
        navigate through root model via given navigation path. supports forward/reverse relations.
    """
    field_or_property = getattr(model, path[0], None)

    if len(path) == 1:
        # end of traversal
        if isinstance(field_or_property, property):
            return field_or_property.fget
        elif isinstance(field_or_property, cached_property):
            return field_or_property.func
        elif callable(field_or_property):
            return field_or_property
        elif isinstance(field_or_property, ManyToManyDescriptor):
            if field_or_property.reverse:
                return field_or_property.rel.target_field  # m2m reverse
            else:
                return field_or_property.field.target_field  # m2m forward
        elif isinstance(field_or_property, ReverseOneToOneDescriptor):
            return field_or_property.related.target_field  # o2o reverse
        elif isinstance(field_or_property, ReverseManyToOneDescriptor):
            return field_or_property.rel.target_field  # type: ignore # foreign reverse
        elif isinstance(field_or_property, ForwardManyToOneDescriptor):
            return field_or_property.field.target_field  # type: ignore # o2o & foreign forward
        else:
            field = model._meta.get_field(path[0])
            if isinstance(field, ForeignObjectRel):
                # case only occurs when relations are traversed in reverse and
                # not via the related_name (default: X_set) but the model name.
                return field.target_field
            else:
                return field
    else:
        if isinstance(field_or_property, (property, cached_property)) or callable(field_or_property):
            if isinstance(field_or_property, property):
                target_model = _follow_return_type(field_or_property.fget)
            elif isinstance(field_or_property, cached_property):
                target_model = _follow_return_type(field_or_property.func)
            else:
                target_model = _follow_return_type(field_or_property)
            if not target_model:
                raise UnableToProceedError(
                    f'could not follow field source through intermediate property "{path[0]}" '
                    f'on model {model}. Please add a type hint on the model\'s property/function '
                    f'to enable traversal of the source path "{".".join(path)}".'
                )
            return _follow_field_source(target_model, path[1:])
        else:
            target_model = model._meta.get_field(path[0]).related_model
            return _follow_field_source(target_model, path[1:])


def _follow_return_type(a_callable):
    target_type = typing.get_type_hints(a_callable).get('return')
    if target_type is None:
        return target_type
    origin, args = _get_type_hint_origin(target_type)
    if origin is typing.Union:
        type_args = [arg for arg in args if arg is not type(None)]  # noqa: E721
        if len(type_args) > 1:
            warn(
                f'could not traverse Union type, because we don\'t know which type to choose '
                f'from {type_args}. Consider terminating "source" on a custom property '
                f'that indicates the expected Optional/Union type. Defaulting to "string"'
            )
            return target_type
        # Optional:
        return type_args[0]
    return target_type


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
            f'This is likely a custom field that does some unknown magic. Maybe '
            f'consider annotating the field/property? Defaulting to "string". (Exception: {exc})'
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
        assert self.__bool__()
        return {'$ref': f'#/components/{self.type}/{self.name}'}


class ComponentRegistry:
    def __init__(self):
        self._components = {}

    def register(self, component: ResolvedComponent):
        if component in self:
            warn(
                f'trying to re-register a {component.type} component with name '
                f'{self._components[component.key].name}. this might lead to '
                f'a incorrect schema. Look out for reused names'
            )
        self._components[component.key] = component

    def register_on_missing(self, component: ResolvedComponent):
        if component not in self:
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
        normalized_choices = []
        for choice in choices:
            if isinstance(choice, str):
                normalized_choices.append((choice, choice))  # simple choice list
            elif isinstance(choice[1], (list, tuple)):
                normalized_choices.extend(choice[1])  # categorized nested choices
            else:
                normalized_choices.append(choice)  # normal 2-tuple form
        overrides[list_hash(list(dict(normalized_choices).keys()))] = name

    if len(spectacular_settings.ENUM_NAME_OVERRIDES) != len(overrides):
        error(
            'ENUM_NAME_OVERRIDES has duplication issues. Encountered multiple names '
            'for the same choice set. Enum naming might be unexpected.'
        )
    return overrides


def list_hash(lst):
    return hashlib.sha256(json.dumps(list(lst), sort_keys=True).encode()).hexdigest()


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

        if api_settings.SCHEMA_COERCE_PATH_PK and parameter == 'pk':
            parameter = 'id'

        if parameter == variable and converter in DJANGO_PATH_CONVERTER_MAPPING:
            return build_parameter_type(
                name=parameter,
                schema=build_basic_type(DJANGO_PATH_CONVERTER_MAPPING[converter]),
                location=OpenApiParameter.PATH,
                enum=enum_values,
            )

    return None


def is_versioning_supported(versioning_class):
    return issubclass(versioning_class, (
        versioning.URLPathVersioning,
        versioning.NamespaceVersioning,
        versioning.AcceptHeaderVersioning
    ))


def operation_matches_version(view, requested_version):
    try:
        version, _ = view.determine_version(view.request, **view.kwargs)
    except exceptions.NotAcceptable:
        return False
    else:
        return str(version) == str(requested_version)


def modify_for_versioning(patterns, method, path, view, requested_version):
    assert view.versioning_class and view.request
    assert requested_version

    view.request.version = requested_version

    if issubclass(view.versioning_class, versioning.URLPathVersioning):
        version_param = view.versioning_class.version_param
        # substitute version variable to emulate request
        path = uritemplate.partial(path, var_dict={version_param: requested_version})
        if isinstance(path, URITemplate):
            path = path.uri
        # emulate router behaviour by injecting substituted variable into view
        view.kwargs[version_param] = requested_version
    elif issubclass(view.versioning_class, versioning.NamespaceVersioning):
        try:
            view.request.resolver_match = get_resolver(
                urlconf=tuple(detype_pattern(p) for p in patterns)
            ).resolve(path)
        except Resolver404:
            error(f"namespace versioning path resolution failed for {path}. Path will be ignored.")
    elif issubclass(view.versioning_class, versioning.AcceptHeaderVersioning):
        # Append the version into request accepted_media_type.
        # e.g "application/json; version=1.0"
        # To allow the AcceptHeaderVersioning negotiator going through.
        if not hasattr(view.request, 'accepted_renderer'):
            # Probably a mock request, content negotation was not performed, so, we do it now.
            negotiated = view.perform_content_negotiation(view.request)
            view.request.accepted_renderer, view.request.accepted_media_type = negotiated
        media_type = _MediaType(view.request.accepted_media_type)
        view.request.accepted_media_type = (
            f'{media_type.full_type}; {view.versioning_class.version_param}={requested_version}'
        )

    return path


def detype_pattern(pattern):
    """
    return an equivalent pattern that accepts arbitrary values for path parameters.
    de-typing the path will ease determining a matching route without having properly
    formatted dummy values for all path parameters.
    """
    if isinstance(pattern, URLResolver):
        return URLResolver(
            pattern=detype_pattern(pattern.pattern),
            urlconf_name=[detype_pattern(p) for p in pattern.url_patterns],
            default_kwargs=pattern.default_kwargs,
            app_name=pattern.app_name,
            namespace=pattern.namespace,
        )
    elif isinstance(pattern, URLPattern):
        return URLPattern(
            pattern=detype_pattern(pattern.pattern),
            callback=pattern.callback,
            default_args=pattern.default_args,
            name=pattern.name,
        )
    elif isinstance(pattern, RoutePattern):
        return RoutePattern(
            route=re.sub(r'<\w+:(\w+)>', r'<\1>', pattern._route),
            name=pattern.name,
            is_endpoint=pattern._is_endpoint
        )
    elif isinstance(pattern, RegexPattern):
        return RegexPattern(
            regex=re.sub(r'\(\?P<(\w+)>.+?\)', r'(?P<\1>[^/]+)', pattern._regex),
            name=pattern.name,
            is_endpoint=pattern._is_endpoint
        )
    else:
        warn(f'unexpected pattern "{pattern}" encountered while simplifying urlpatterns.')
        return pattern


def normalize_result_object(result):
    """ resolve non-serializable objects like lazy translation strings and OrderedDict """
    if isinstance(result, dict) or isinstance(result, OrderedDict):
        return {k: normalize_result_object(v) for k, v in result.items()}
    if isinstance(result, list) or isinstance(result, tuple):
        return [normalize_result_object(v) for v in result]
    if isinstance(result, Promise):
        return str(result)
    for base_type in [bool, int, float, str]:
        if isinstance(result, base_type):
            return base_type(result)  # coerce basic sub types
    return result


def sanitize_result_object(result):
    # warn about and resolve operationId collisions with suffixes
    operations = defaultdict(list)
    for path, methods in result['paths'].items():
        for method, operation in methods.items():
            operations[operation['operationId']].append((path, method))
    for operation_id, paths in operations.items():
        if len(paths) == 1:
            continue
        warn(f'operationId "{operation_id}" has collisions {paths}. resolving with numeral suffixes.')
        for idx, (path, method) in enumerate(sorted(paths)[1:], start=2):
            suffix = str(idx) if spectacular_settings.CAMELIZE_NAMES else f'_{idx}'
            result['paths'][path][method]['operationId'] += suffix

    return result


def camelize_operation(path, operation):
    for path_variable in re.findall(r'\{(\w+)\}', path):
        path = path.replace(
            f'{{{path_variable}}}',
            f'{{{inflection.camelize(path_variable, False)}}}'
        )

    for parameter in operation.get('parameters', []):
        if parameter['in'] == OpenApiParameter.PATH:
            parameter['name'] = inflection.camelize(parameter['name'], False)

    operation['operationId'] = inflection.camelize(operation['operationId'], False)

    return path, operation


def build_mock_request(method, path, view, original_request, **kwargs):
    request = getattr(APIRequestFactory(), method.lower())(path=path)
    request = view.initialize_request(request)
    return request


def set_query_parameters(url, **kwargs) -> str:
    """ deconstruct url, safely attach query parameters in kwargs, and serialize again """
    scheme, netloc, path, params, query, fragment = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(query)
    query.update({k: v for k, v in kwargs.items() if v is not None})
    query = urllib.parse.urlencode(query, doseq=True)
    return urllib.parse.urlunparse((scheme, netloc, path, params, query, fragment))


def get_relative_url(url: str) -> str:
    scheme, netloc, path, params, query, fragment = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse(('', '', path, params, query, fragment))


def _get_type_hint_origin(hint):
    """ graceful fallback for py 3.8 typing functionality """
    if sys.version_info >= (3, 8):
        return typing.get_origin(hint), typing.get_args(hint)
    else:
        origin = getattr(hint, '__origin__', None)
        args = getattr(hint, '__args__', None)
        origin = {
            typing.List: list,
            typing.Dict: dict,
            typing.Tuple: tuple,
            typing.Set: set,
            typing.FrozenSet: frozenset
        }.get(origin, origin)
        return origin, args


def resolve_type_hint(hint):
    """ resolve return value type hints to schema """
    origin, args = _get_type_hint_origin(hint)

    if origin is None and is_basic_type(hint, allow_none=False):
        return build_basic_type(hint)
    elif origin is list or hint is list:
        return build_array_type(
            resolve_type_hint(args[0]) if args else build_basic_type(OpenApiTypes.OBJECT)
        )
    elif origin is tuple:
        return build_array_type(
            schema=build_basic_type(args[0]),
            max_length=len(args),
            min_length=len(args),
        )
    elif origin is dict or origin is defaultdict or origin is OrderedDict:
        schema = build_basic_type(OpenApiTypes.OBJECT)
        if args and args[1] is not typing.Any:
            schema['additionalProperties'] = resolve_type_hint(args[1])
        return schema
    elif origin is set:
        return build_array_type(resolve_type_hint(args[0]))
    elif origin is frozenset:
        return build_array_type(resolve_type_hint(args[0]))
    elif hasattr(typing, 'Literal') and origin is typing.Literal:
        # python >= 3.8
        schema = {'enum': list(args)}
        if all(type(args[0]) is type(choice) for choice in args):
            schema.update(build_basic_type(type(args[0])))
        return schema
    elif hasattr(typing, 'TypedDict') and isinstance(hint, typing._TypedDictMeta):
        return build_object_type(
            properties={
                k: resolve_type_hint(v) for k, v in typing.get_type_hints(hint).items()
            }
        )
    elif origin is typing.Union:
        type_args = [arg for arg in args if arg is not type(None)]  # noqa: E721
        if len(type_args) > 1:
            schema = {'oneOf': [resolve_type_hint(arg) for arg in type_args]}
        else:
            schema = resolve_type_hint(type_args[0])
        if type(None) in args:
            schema['nullable'] = True
        return schema
    else:
        raise UnableToProceedError()
