import re
from unittest import mock

import pytest
from django.db import models
from django.urls import include, path, re_path
from rest_framework import routers, serializers, viewsets
from rest_framework.routers import SimpleRouter

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from tests import assert_schema, generate_schema


class Root(models.Model):
    name = models.CharField(max_length=255)


class Child(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(Root, on_delete=models.CASCADE)


class RootSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Root
        fields = ('name',)


class ChildSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Child
        fields = ('name', 'parent',)


@pytest.mark.contrib('drf_nested_routers')
@mock.patch('drf_spectacular.settings.spectacular_settings.SCHEMA_COERCE_PATH_PK_NESTED', True)
def test_drf_nested_routers_basic_example(no_warnings):
    from rest_framework_nested.routers import NestedSimpleRouter

    class RootViewSet(viewsets.ModelViewSet):
        serializer_class = RootSerializer
        queryset = Root.objects.all()

    class ChildViewSet(viewsets.ModelViewSet):
        serializer_class = ChildSerializer
        queryset = Child.objects.all()

    router = SimpleRouter()
    router.register('root', RootViewSet, basename='root')

    root_router = NestedSimpleRouter(router, r'root', lookup='parent')
    root_router.register(r'child', ChildViewSet, basename='child')

    urlpatterns = [
        re_path(r'^', include(router.urls)),
        re_path(r'^', include(root_router.urls)),
    ]
    schema = generate_schema(None, patterns=urlpatterns)
    assert_schema(schema, 'tests/contrib/test_drf_nested_routers.yml')
    assert schema


@pytest.mark.contrib('drf_nested_routers')
@mock.patch('drf_spectacular.settings.spectacular_settings.SCHEMA_COERCE_PATH_PK_NESTED', False)
def test_drf_nested_routers_basic_example_disable_coerce_nested_pks(no_warnings):
    from rest_framework_nested.routers import NestedSimpleRouter

    parameters = [OpenApiParameter('parent_pk', OpenApiTypes.INT, OpenApiParameter.PATH)]
    transforms = [lambda x: re.sub(r'\bparent_pk\b', 'parent_id', x)]

    class RootViewSet(viewsets.ModelViewSet):
        serializer_class = RootSerializer
        queryset = Root.objects.all()

    @extend_schema_view(
        list=extend_schema(parameters=parameters),
        create=extend_schema(parameters=parameters),
        retrieve=extend_schema(parameters=parameters),
        update=extend_schema(parameters=parameters),
        partial_update=extend_schema(parameters=parameters),
        destroy=extend_schema(parameters=parameters),
    )
    class ChildViewSet(viewsets.ModelViewSet):
        serializer_class = ChildSerializer
        queryset = Child.objects.all()

    router = SimpleRouter()
    router.register('root', RootViewSet, basename='root')

    root_router = NestedSimpleRouter(router, r'root', lookup='parent')
    root_router.register(r'child', ChildViewSet, basename='child')

    urlpatterns = [
        re_path(r'^', include(router.urls)),
        re_path(r'^', include(root_router.urls)),
    ]
    schema = generate_schema(None, patterns=urlpatterns)
    assert_schema(schema, 'tests/contrib/test_drf_nested_routers.yml', transforms=transforms)
    assert schema


@pytest.mark.contrib('rest_framework_nested')
def test_drf_nested_routers_basic_example_variation(no_warnings):
    from rest_framework_nested.routers import NestedSimpleRouter

    class RootViewSet(viewsets.ModelViewSet):
        queryset = Root.objects.all()
        serializer_class = RootSerializer
        lookup_value_regex = "[0-9]+"

    class ChildViewSet(viewsets.ModelViewSet):
        serializer_class = ChildSerializer

        def get_queryset(self):
            return Child.objects.filter(id=self.kwargs.get("parent_pk"))

    router = routers.SimpleRouter()
    router.register('root', RootViewSet, basename='root')

    root_router = NestedSimpleRouter(router, r'root', lookup='parent')
    root_router.register(r'child', ChildViewSet, basename='child')

    urlpatterns = [
        path(r'', include(router.urls)),
        path(r'', include(root_router.urls)),
    ]
    generate_schema(None, patterns=urlpatterns)
