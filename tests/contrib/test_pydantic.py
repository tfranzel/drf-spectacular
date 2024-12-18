import sys
from decimal import Decimal
from typing import List

import pytest
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema
from tests import assert_schema, generate_schema

try:
    from pydantic import BaseModel, computed_field
    from pydantic.dataclasses import dataclass
except ImportError:
    class BaseModel:  # type: ignore
        pass

    def dataclass(f):
        return f

    def computed_field(f):
        return f


@dataclass
class C:
    id: int


class B(BaseModel):
    id: int
    c: List[C]


class A(BaseModel):
    id: int
    b: B
    d: Decimal

    @computed_field  # type: ignore[misc]
    @property
    def x(self) -> int:
        return 42


@pytest.mark.contrib('pydantic')
@pytest.mark.skipif(sys.version_info < (3, 7), reason='python 3.7+ is required by package')
def test_pydantic_decoration(no_warnings):
    class XAPIView(APIView):
        @extend_schema(request=A, responses=B)
        def post(self, request):
            pass  # pragma: no cover

    schema = generate_schema('/x', view=XAPIView)
    assert_schema(schema, 'tests/contrib/test_pydantic.yml')


@pytest.mark.contrib('pydantic')
@pytest.mark.skipif(sys.version_info < (3, 7), reason='python 3.7+ is required by package')
def test_pydantic_as_query_parameters(no_warnings):
    class QueryParams(BaseModel):
        foo: int
        bar: str

    class XAPIView(APIView):
        @extend_schema(responses=str, parameters=[QueryParams])
        def get(self, request):
            pass  # pragma: no cover

    schema = generate_schema('/x', view=XAPIView)
    assert schema['paths']['/x']['get']['parameters'] == [
        {'in': 'query', 'name': 'bar', 'required': True, 'schema': {'title': 'Bar', 'type': 'string'}},
        {'in': 'query', 'name': 'foo', 'required': True, 'schema': {'title': 'Foo', 'type': 'integer'}}
    ]
