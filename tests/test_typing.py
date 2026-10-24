"""
Usage of the entry points that extension authors and ``AutoSchema`` subclasses call,
type checked with ``disallow_untyped_calls`` (see ``[mypy-tests.test_typing]`` in tox.ini).
Downstream projects running ``mypy --strict`` hit exactly these calls.
"""
from typing import Any, Optional

from django.urls import path
from rest_framework import generics, serializers

from drf_spectacular.extensions import OpenApiSerializerExtension, OpenApiSerializerFieldExtension
from drf_spectacular.generators import EndpointEnumerator, SchemaGenerator
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import force_instance
from drf_spectacular.utils import Direction, _SchemaType


class TypingHiddenField(serializers.CharField):
    pass


class TypingSerializer(serializers.Serializer):
    hidden = TypingHiddenField()
    visible = serializers.IntegerField()


class TypingHiddenFieldExtension(OpenApiSerializerFieldExtension):
    target_class = TypingHiddenField

    def map_serializer_field(self, auto_schema: AutoSchema, direction: Direction) -> Optional[_SchemaType]:
        return None


class TypingSerializerExtension(OpenApiSerializerExtension):
    target_class = TypingSerializer

    def map_serializer(self, auto_schema: AutoSchema, direction: Direction) -> _SchemaType:
        schema = auto_schema._map_serializer(self.target, direction, bypass_extensions=True)
        schema['x-extended'] = True
        return schema


class TypingAutoSchema(AutoSchema):
    def _map_basic_serializer(self, serializer: Any, direction: Direction) -> _SchemaType:
        schema = super()._map_basic_serializer(serializer, direction)
        schema['x-fields'] = sorted(force_instance(serializer).fields)
        return schema


class TypingView(generics.RetrieveAPIView):
    serializer_class = TypingSerializer
    schema = TypingAutoSchema()


def test_typed_entry_points(no_warnings: Any) -> None:
    patterns = [path('x/', TypingView.as_view())]

    endpoints = EndpointEnumerator(patterns).get_api_endpoints()
    assert [(route, method) for route, _, method, _ in endpoints] == [('/x/', 'GET')]

    schema = SchemaGenerator(patterns=patterns).get_schema(request=None, public=True)
    component = schema['components']['schemas']['Typing']
    assert component['x-extended'] is True
    assert component['x-fields'] == ['hidden', 'visible']
    assert component['properties'] == {'visible': {'type': 'integer'}}
