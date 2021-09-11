import pytest
from django.db import models
from django.urls import include, re_path, path
from rest_framework import viewsets, serializers, routers
from rest_framework.routers import SimpleRouter

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
