import collections
import json
import re
import sys
import typing
from datetime import datetime
from enum import Enum

import pytest
from django import __version__ as DJANGO_VERSION
from django.conf.urls import include
from django.db import models
from django.urls import re_path
from rest_framework import generics, serializers

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import (
    analyze_named_regex_pattern, build_basic_type, detype_pattern, follow_field_source,
    force_instance, is_field, is_serializer, resolve_type_hint,
)
from drf_spectacular.validation import validate_schema
from tests import generate_schema

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


def test_is_serializer():
    assert not is_serializer(serializers.SlugField)
    assert not is_serializer(serializers.SlugField())

    assert not is_serializer(models.CharField)
    assert not is_serializer(models.CharField())

    assert is_serializer(serializers.Serializer)
    assert is_serializer(serializers.Serializer())


def test_is_field():
    assert is_field(serializers.SlugField)
    assert is_field(serializers.SlugField())

    assert not is_field(models.CharField)
    assert not is_field(models.CharField())

    assert not is_field(serializers.Serializer)
    assert not is_field(serializers.Serializer())


def test_force_instance():
    assert isinstance(force_instance(serializers.CharField), serializers.CharField)
    assert force_instance(5) == 5
    assert force_instance(dict) == dict


def test_follow_field_source_forward_reverse(no_warnings):
    class FFS1(models.Model):
        id = models.UUIDField(primary_key=True)
        field_bool = models.BooleanField()

    class FFS2(models.Model):
        ffs1 = models.ForeignKey(FFS1, on_delete=models.PROTECT)

    class FFS3(models.Model):
        id = models.CharField(primary_key=True, max_length=3)
        ffs2 = models.ForeignKey(FFS2, on_delete=models.PROTECT)
        field_float = models.FloatField()

    forward_field = follow_field_source(FFS3, ['ffs2', 'ffs1', 'field_bool'])
    reverse_field = follow_field_source(FFS1, ['ffs2', 'ffs3', 'field_float'])
    forward_model = follow_field_source(FFS3, ['ffs2', 'ffs1'])
    reverse_model = follow_field_source(FFS1, ['ffs2', 'ffs3'])

    assert isinstance(forward_field, models.BooleanField)
    assert isinstance(reverse_field, models.FloatField)
    assert isinstance(forward_model, models.UUIDField)
    assert isinstance(reverse_model, models.CharField)

    auto_schema = AutoSchema()
    assert auto_schema._map_model_field(forward_field, None)['type'] == 'boolean'
    assert auto_schema._map_model_field(reverse_field, None)['type'] == 'number'
    assert auto_schema._map_model_field(forward_model, None)['type'] == 'string'
    assert auto_schema._map_model_field(reverse_model, None)['type'] == 'string'


def test_detype_patterns_with_module_includes(no_warnings):
    detype_pattern(
        pattern=re_path(r'^', include('tests.test_fields'))
    )


NamedTupleA = collections.namedtuple("NamedTupleA", "a, b")


class NamedTupleB(typing.NamedTuple):
    a: int
    b: str


class LanguageEnum(str, Enum):
    EN = 'en'
    DE = 'de'


# Make sure we can deal with plain Enums that are not handled by DRF.
# The second base class makes this work for DRF.
class InvalidLanguageEnum(Enum):
    EN = 'en'
    DE = 'de'


TD1 = TypedDict('TD1', {"foo": int, "bar": typing.List[str]})
TD2 = TypedDict('TD2', {"foo": str, "bar": typing.Dict[str, int]})


TYPE_HINT_TEST_PARAMS = [
    (
        typing.Optional[int],
        {'type': 'integer', 'nullable': True}
    ), (
        typing.List[int],
        {'type': 'array', 'items': {'type': 'integer'}}
    ), (
        typing.List[typing.Dict[str, int]],
        {'type': 'array', 'items': {'type': 'object', 'additionalProperties': {'type': 'integer'}}}
    ), (
        list,
        {'type': 'array', 'items': {}}
    ), (
        typing.Tuple[int, int, int],
        {'type': 'array', 'items': {'type': 'integer'}, 'minLength': 3, 'maxLength': 3}
    ), (
        typing.Set[datetime],
        {'type': 'array', 'items': {'type': 'string', 'format': 'date-time'}}
    ), (
        typing.FrozenSet[datetime],
        {'type': 'array', 'items': {'type': 'string', 'format': 'date-time'}}
    ), (
        typing.Dict[str, int],
        {'type': 'object', 'additionalProperties': {'type': 'integer'}}
    ), (
        typing.Dict[str, str],
        {'type': 'object', 'additionalProperties': {'type': 'string'}}
    ), (
        typing.Dict[str, typing.List[int]],
        {'type': 'object', 'additionalProperties': {'type': 'array', 'items': {'type': 'integer'}}}
    ), (
        dict,
        {'type': 'object', 'additionalProperties': {}}
    ), (
        typing.Union[int, str],
        {'oneOf': [{'type': 'integer'}, {'type': 'string'}]}
    ), (
        typing.Union[int, str, None],
        {'oneOf': [{'type': 'integer'}, {'type': 'string'}], 'nullable': True}
    ), (
        typing.Optional[typing.Union[str, int]],
        {'oneOf': [{'type': 'string'}, {'type': 'integer'}], 'nullable': True}
    ), (
        LanguageEnum,
        {'enum': ['en', 'de'], 'type': 'string'}
    ), (
        InvalidLanguageEnum,
        {'enum': ['en', 'de']}
    ), (
        TD1,
        {
            'type': 'object',
            'properties': {
                'foo': {'type': 'integer'},
                'bar': {'type': 'array', 'items': {'type': 'string'}}
            }
        }
    ), (
        typing.List[TD2],
        {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'foo': {'type': 'string'},
                    'bar': {'type': 'object', 'additionalProperties': {'type': 'integer'}}
                }
            }
        }
    ), (
        NamedTupleB,
        {
            'type': 'object',
            'properties': {'a': {'type': 'integer'}, 'b': {'type': 'string'}},
            'required': ['a', 'b']
        }
    )
]


if DJANGO_VERSION > '3':
    from django.db.models.enums import TextChoices  # only available in Django>3

    class LanguageChoices(TextChoices):
        EN = 'en'
        DE = 'de'

    TYPE_HINT_TEST_PARAMS.append((
        LanguageChoices,
        {'enum': ['en', 'de'], 'type': 'string'}
    ))

if sys.version_info >= (3, 7):
    TYPE_HINT_TEST_PARAMS.append((
        typing.Iterable[NamedTupleA],
        {
            'type': 'array',
            'items': {'type': 'object', 'properties': {'a': {}, 'b': {}}, 'required': ['a', 'b']}
        }
    ))

if sys.version_info >= (3, 8):
    # Literal only works for python >= 3.8 despite typing_extensions, because it
    # behaves slightly different w.r.t. __origin__
    TYPE_HINT_TEST_PARAMS.append((
        typing.Literal['x', 'y'],
        {'enum': ['x', 'y'], 'type': 'string'}
    ))

if sys.version_info >= (3, 9):
    TYPE_HINT_TEST_PARAMS.append((
        dict[str, int],
        {'type': 'object', 'additionalProperties': {'type': 'integer'}}
    ))


@pytest.mark.parametrize(['type_hint', 'ref_schema'], TYPE_HINT_TEST_PARAMS)
def test_type_hint_extraction(no_warnings, type_hint, ref_schema):
    def func() -> type_hint:
        pass  # pragma: no cover

    # check expected resolution
    schema = resolve_type_hint(typing.get_type_hints(func).get('return'))
    assert json.dumps(schema) == json.dumps(ref_schema)

    # check schema validity
    class XSerializer(serializers.Serializer):
        x = serializers.SerializerMethodField()
    XSerializer.get_x = func

    class XView(generics.RetrieveAPIView):
        serializer_class = XSerializer

    validate_schema(generate_schema('/x', view=XView))


@pytest.mark.parametrize(['pattern', 'output'], [
    ('(?P<t1><,()(())(),)', {'t1': '<,()(())(),'}),
    (r'(?P<t1>.\\)', {'t1': r'.\\'}),
    (r'(?P<t1>.\\\\)', {'t1': r'.\\\\'}),
    (r'(?P<t1>.\))', {'t1': r'.\)'}),
    (r'(?P<t1>)', {'t1': r''}),
    (r'(?P<t1>.[\(]{2})', {'t1': r'.[\(]{2}'}),
    (r'(?P<t1>(.))/\(t/(?P<t2>\){2}()\({2}().*)', {'t1': '(.)', 't2': r'\){2}()\({2}().*'}),
])
def test_analyze_named_regex_pattern(no_warnings, pattern, output):
    re.compile(pattern)  # check validity of regex
    assert analyze_named_regex_pattern(pattern) == output


def test_unknown_basic_type(capsys):
    build_basic_type(object)
    assert 'could not resolve type for "<class \'object\'>' in capsys.readouterr().err
