import inspect
import sys

from django import __version__ as DJANGO_VERSION
from rest_framework import fields, serializers

from drf_spectacular.types import OPENAPI_TYPE_MAPPING, PYTHON_TYPE_MAPPING, OpenApiTypes
from drf_spectacular.utils import PolymorphicProxySerializer


def warn(msg):
    print(f'WARNING: {msg}', file=sys.stderr)


def anyisinstance(obj, type_list):
    return any([isinstance(obj, t) for t in type_list])


def force_serializer_instance(serializer):
    if inspect.isclass(serializer) and issubclass(serializer, serializers.BaseSerializer):
        return serializer()
    else:
        return serializer


def is_serializer(obj):
    return anyisinstance(
        force_serializer_instance(obj),
        [serializers.BaseSerializer, PolymorphicProxySerializer, fields.Field]
    )


def resolve_basic_type(type_):
    """
    resolve either enum or actual type and yield schema template for modification
    """
    if type_ in OPENAPI_TYPE_MAPPING:
        return dict(OPENAPI_TYPE_MAPPING[type_])
    elif type_ in PYTHON_TYPE_MAPPING:
        return dict(OPENAPI_TYPE_MAPPING[PYTHON_TYPE_MAPPING[type_]])
    elif type_ is None or type(type_) is None:
        return dict(OPENAPI_TYPE_MAPPING[OpenApiTypes.NONE])
    else:
        warn(f'could not resolve type "{type_}". defaulting to "string"')
        return dict(OPENAPI_TYPE_MAPPING[OpenApiTypes.STR])


def _follow_field_source(model, path):
    field_or_property = getattr(model, path[0])

    if len(path) == 1:
        # end of traversal
        if isinstance(field_or_property, property):
            return field_or_property.fget
        else:
            if DJANGO_VERSION.startswith('2'):
                # trying to access the field through the DeferredAttribute will fail in an
                # endless loop. bypass this issue by fishing it out of the meta field list.
                field_name = field_or_property.field_name
                return [f for f in model._meta.fields if f.name == field_name][0]
            else:
                return field_or_property.field
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
