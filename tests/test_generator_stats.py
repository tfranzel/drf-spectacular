import inspect

import pytest

from drf_spectacular.drainage import GENERATOR_STATS


def test_known_attribute_access_succeeds():
    assert hasattr(GENERATOR_STATS, 'silent')


def test_unknown_attribute_access_fails():
    with pytest.raises(AttributeError):
        getattr(GENERATOR_STATS, '__spam__')


def test_inspect_unwrap():
    assert inspect.unwrap(GENERATOR_STATS) is GENERATOR_STATS
