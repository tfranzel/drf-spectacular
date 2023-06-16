import sys
import typing

import pytest
from django.urls import path
from rest_framework.decorators import api_view

from drf_spectacular.utils import extend_schema, extend_schema_serializer
from tests import assert_schema, generate_schema


@pytest.mark.contrib('rest_framework_dataclasses')
@pytest.mark.skipif(sys.version_info < (3, 7), reason='dataclass required by package')
def test_rest_framework_dataclasses(no_warnings):
    from dataclasses import dataclass

    from rest_framework_dataclasses.serializers import DataclassSerializer

    @dataclass
    class PersonDetail:
        name: str
        length: int

    @dataclass
    class Person:
        name: str
        length: int
        detail: PersonDetail

    @dataclass
    class Group:
        name: str
        leader: Person
        members: typing.List[Person]

    class GroupSerializer(DataclassSerializer):
        class Meta:
            dataclass = Group

    class GroupSerializer2(DataclassSerializer):
        class Meta:
            dataclass = Group
            ref_name = "CustomGroupNameFromRefName"

    @extend_schema_serializer(component_name='CustomGroupNameFromSerializerDecoration')
    class GroupSerializer3(DataclassSerializer[Group]):
        class Meta:
            dataclass = Group

    @extend_schema_serializer(component_name='CustomGroupNameFromDecoration')
    @dataclass
    class Group2:
        name: str
        leader: Person
        members: typing.List[Person]

    @extend_schema(responses=GroupSerializer)
    @api_view(['GET'])
    def named(request):
        pass  # pragma: no cover

    @extend_schema(responses=DataclassSerializer(dataclass=Person))
    @api_view(['GET'])
    def anonymous(request):
        pass  # pragma: no cover

    @extend_schema(responses=GroupSerializer2(many=True))
    @api_view(['GET'])
    def custom_name_via_ref(request):
        pass  # pragma: no cover

    @extend_schema(responses=DataclassSerializer(dataclass=Group2))
    @api_view(['GET'])
    def custom_name_via_decoration(request):
        pass  # pragma: no cover

    @extend_schema(responses=GroupSerializer3)
    @api_view(['GET'])
    def custom_name_via_serializer_decoration(request):
        pass  # pragma: no cover

    urlpatterns = [
        path('named', named),
        path('anonymous', anonymous),
        path('custom_name_via_ref', custom_name_via_ref),
        path('custom_name_via_decoration', custom_name_via_decoration),
        path('custom_name_via_serializer_decoration', custom_name_via_serializer_decoration)
    ]
    assert_schema(
        generate_schema(None, patterns=urlpatterns),
        'tests/contrib/test_rest_framework_dataclasses.yml'
    )
