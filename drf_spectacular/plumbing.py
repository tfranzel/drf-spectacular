import inspect
import sys
from collections.abc import Hashable

from django import __version__ as DJANGO_VERSION
from rest_framework import fields, serializers

from drf_spectacular.types import OPENAPI_TYPE_MAPPING, PYTHON_TYPE_MAPPING, OpenApiTypes
from drf_spectacular.utils import PolymorphicProxySerializer


def warn(msg):
    print(f'WARNING: {msg}', file=sys.stderr)


def anyisinstance(obj, type_list):
    return any([isinstance(obj, t) for t in type_list])


def force_instance(serializer_or_field):
    if not inspect.isclass(serializer_or_field):
        return serializer_or_field
    elif issubclass(serializer_or_field, (serializers.BaseSerializer, fields.Field)):
        return serializer_or_field()
    else:
        return serializer_or_field


def is_serializer(obj):
    return anyisinstance(
        force_instance(obj),
        [serializers.BaseSerializer, PolymorphicProxySerializer]
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
        warn(f'could not resolve type "{obj}". defaulting to "string"')
        return dict(OPENAPI_TYPE_MAPPING[OpenApiTypes.STR])


def build_array_type(schema):
    return {
        'type': 'array',
        'items': schema,
    }


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
