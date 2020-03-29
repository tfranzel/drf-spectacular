import inspect
import sys
from abc import ABCMeta
from collections import defaultdict
from collections.abc import Hashable
from typing import List, Type, Optional, TypeVar, Union, Generic

from django import __version__ as DJANGO_VERSION
from django.utils.module_loading import import_string
from rest_framework import fields, serializers

from drf_spectacular.settings import spectacular_settings
from drf_spectacular.types import OPENAPI_TYPE_MAPPING, PYTHON_TYPE_MAPPING, OpenApiTypes

T = TypeVar('T')


class GeneratorStats:
    warn_counter = 0


GENERATOR_STATS = GeneratorStats()


def warn(msg):
    GENERATOR_STATS.warn_counter += 1
    print(f'WARNING #{GENERATOR_STATS.warn_counter}: {msg}', file=sys.stderr)


def reset_generator_stats():
    GENERATOR_STATS.warn_counter = 0


def anyisinstance(obj, type_list):
    return any([isinstance(obj, t) for t in type_list])


def get_class(obj):
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


def get_field_from_model(model, field):
    """
    this is a Django 2.2 compatibility function to access a field through a Deferred Attribute
    """
    if DJANGO_VERSION.startswith('2'):
        # trying to access the field through the DeferredAttribute will fail in an
        # endless loop. bypass this issue by fishing it out of the meta field list.
        field_name = field.field_name
        return [f for f in model._meta.fields if f.name == field_name][0]
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
        model = field_or_property.field.related_model
        return follow_field_source(model, path[1:])


def follow_field_source(model, path):
    """
    a model traversal chain "foreignkey.foreignkey.value" can either end with an actual model field
    instance "value" or a model property function named "value". differentiate the cases.

    :return: models.Field or function object
    """
    try:
        return _follow_field_source(model, path)
    except:  # noqa: E722
        warn(
            f'could not resolve field on model {model} with path "{".".join(path)}". '
            f'this is likely a custom field that does some unknown magic. maybe '
            f'consider annotating the field? defaulting to "string".'
        )

        def dummy_property(obj) -> str:
            pass

        return dummy_property


def alpha_operation_sorter(endpoint):
    """ sort endpoints first alphanumerically by path, then by method order """
    path, method, callback = endpoint
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
        output = defaultdict(dict)
        # build tree from flat registry
        for component in self._components.values():
            output[component.type][component.name] = component.schema
        # add/override extra components
        for extra_type, extra_component_dict in extra_components.items():
            for component_name, component_schema in extra_component_dict.items():
                output[extra_type][component_name] = component_schema
        # sort by component type then by name
        return {
            type: {name: output[type][name] for name in output[type].keys()}
            for type in sorted(output.keys(), reverse=True)
        }


class OpenApiGeneratorExtension(Generic[T], metaclass=ABCMeta):
    _registry: List[T] = []
    target_class: Union[None, str, Type[object]] = None
    match_subclasses = False

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
            return issubclass(get_class(target), cls.target_class)
        else:
            return get_class(target) == cls.target_class

    @classmethod
    def get_match(cls, target) -> Optional[T]:
        for extension in cls._registry:
            if extension._matches(target):
                return extension(target)
        return None
