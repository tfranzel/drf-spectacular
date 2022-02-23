import pytest
from django.urls import path
from rest_framework import serializers
from rest_framework.decorators import api_view

from drf_spectacular.utils import extend_schema
from tests import assert_schema, generate_schema

try:
    from rest_framework_recursive.fields import RecursiveField
except ImportError:
    from rest_framework.fields import Field as RecursiveField


class TreeSerializer(serializers.Serializer):
    name = serializers.CharField()
    children = serializers.ListField(child=RecursiveField())


class TreeManySerializer(serializers.Serializer):
    name = serializers.CharField()
    children = RecursiveField(many=True)


class PingSerializer(serializers.Serializer):
    ping_id = serializers.IntegerField()
    pong = RecursiveField('PongSerializer', required=False)


class PongSerializer(serializers.Serializer):
    pong_id = serializers.IntegerField()
    ping = PingSerializer()


class LinkSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=25)
    next = RecursiveField(allow_null=True)


@pytest.mark.contrib('rest_framework_recursive')
def test_rest_framework_recursive(no_warnings):
    @extend_schema(request=TreeSerializer, responses=TreeSerializer)
    @api_view(['POST'])
    def tree(request):
        pass  # pragma: no cover

    @extend_schema(request=TreeManySerializer, responses=TreeManySerializer)
    @api_view(['POST'])
    def tree_many(request):
        pass  # pragma: no cover

    @extend_schema(request=PingSerializer, responses=PingSerializer)
    @api_view(['POST'])
    def pong(request):
        pass  # pragma: no cover

    @extend_schema(request=LinkSerializer, responses=LinkSerializer)
    @api_view(['POST'])
    def link(request):
        pass  # pragma: no cover

    urlpatterns = [
        path('tree', tree),
        path('tree_many', tree_many),
        path('pong', pong),
        path('link', link)
    ]
    assert_schema(
        generate_schema(None, patterns=urlpatterns),
        'tests/contrib/test_rest_framework_recursive.yml'
    )
