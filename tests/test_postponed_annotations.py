from __future__ import annotations

import sys
import typing

import pytest

from drf_spectacular.plumbing import resolve_type_hint

if sys.version_info >= (3, 11):
    class TDPostponed(typing.TypedDict):
        a: str
        b: typing.NotRequired[str]
        c: typing.NotRequired[typing.Annotated[str, 'meta']]

    class TDPostponedPartial(typing.TypedDict, total=False):
        a: str
        b: typing.Required[str]

    class TDPostponedChild(TDPostponedPartial):
        c: str
        d: typing.NotRequired[str]


@pytest.mark.skipif(sys.version_info < (3, 11), reason='Required/NotRequired need python >= 3.11')
def test_typeddict_qualifiers_with_postponed_annotations():
    # with postponed annotations, TypedDict.__required_keys__ ignores (Not)Required
    assert resolve_type_hint(TDPostponed) == {
        'type': 'object',
        'properties': {
            'a': {'type': 'string'},
            'b': {'type': 'string'},
            'c': {'type': 'string'},
        },
        'required': ['a'],
    }
    assert resolve_type_hint(TDPostponedPartial)['required'] == ['b']
    assert resolve_type_hint(TDPostponedChild)['required'] == ['b', 'c']
