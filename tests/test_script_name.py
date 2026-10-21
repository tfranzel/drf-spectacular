import pytest
from django.urls import clear_script_prefix, set_script_prefix
from rest_framework import serializers, viewsets
from rest_framework.response import Response

from tests import generate_schema


class AnimalSerializer(serializers.Serializer):
    name = serializers.CharField()


class AnimalViewSet(viewsets.ViewSet):
    serializer_class = AnimalSerializer

    def list(self, request):
        pass  # pragma: no cover

    def retrieve(self, request, pk):
        pass  # pragma: no cover

    def summary(self, request):
        return Response()  # pragma: no cover


@pytest.fixture(autouse=True)
def reset_script_prefix():
    yield
    clear_script_prefix()


def test_paths_without_script_prefix():
    schema = generate_schema('animals', AnimalViewSet)
    assert sorted(schema['paths']) == ['/animals/', '/animals/{id}/']


def test_paths_prefixed_with_script_name():
    # what the WSGI/ASGI handlers do when the app is served under a
    # prefix taken from the SCRIPT_NAME environ variable / root_path
    set_script_prefix('/my-prefix/')
    schema = generate_schema('animals', AnimalViewSet)
    assert sorted(schema['paths']) == [
        '/my-prefix/animals/',
        '/my-prefix/animals/{id}/',
    ]


def test_script_prefix_without_trailing_slash():
    set_script_prefix('/my-prefix')
    schema = generate_schema('animals', AnimalViewSet)
    assert sorted(schema['paths']) == [
        '/my-prefix/animals/',
        '/my-prefix/animals/{id}/',
    ]


def test_script_prefix_is_not_doubled():
    # a path that already carries the prefix (e.g. via an explicit
    # SCHEMA_PATH_PREFIX_INSERT) must not be prefixed twice
    set_script_prefix('/my-prefix/')
    schema = generate_schema('/my-prefix/animals', AnimalViewSet)
    assert sorted(schema['paths']) == [
        '/my-prefix/animals/',
        '/my-prefix/animals/{id}/',
    ]
