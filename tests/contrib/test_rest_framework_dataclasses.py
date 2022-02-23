import sys
import typing

import pytest
from django.urls import path
from rest_framework.decorators import api_view

from drf_spectacular.utils import extend_schema
from tests import assert_schema, generate_schema


@pytest.mark.contrib('rest_framework_dataclasses')
@pytest.mark.skipif(sys.version_info < (3, 7), reason='dataclass required by package')
def test_rest_framework_dataclasses(no_warnings):
    from dataclasses import dataclass

    from rest_framework_dataclasses.serializers import DataclassSerializer

    @dataclass
    class Person:
        name: str
        length: int

    @dataclass
    class Group:
        name: str
        leader: Person
        members: typing.List[Person]

    class GroupSerializer(DataclassSerializer):
        class Meta:
            dataclass = Group

    @extend_schema(responses=GroupSerializer)
    @api_view(['GET'])
    def named(request):
        pass  # pragma: no cover

    @extend_schema(responses=DataclassSerializer(dataclass=Person))
    @api_view(['GET'])
    def anonymous(request):
        pass  # pragma: no cover

    urlpatterns = [
        path('named', named),
        path('anonymous', anonymous),
    ]
    assert_schema(
        generate_schema(None, patterns=urlpatterns),
        'tests/contrib/test_rest_framework_dataclasses.yml'
    )
