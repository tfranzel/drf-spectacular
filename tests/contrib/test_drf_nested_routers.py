from unittest import mock

import pytest
from django.db import models
from django.urls import include, re_path
from rest_framework import serializers, viewsets
from rest_framework.routers import SimpleRouter

from tests import assert_schema, generate_schema


class Root(models.Model):
    id = models.UUIDField(primary_key=True)
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


def _generate_nested_routers_schema(root_viewset, child_viewset):
    from rest_framework_nested.routers import NestedSimpleRouter

    router = SimpleRouter()
    router.register('root', root_viewset, basename='root')

    root_router = NestedSimpleRouter(router, r'root', lookup='parent')
    root_router.register(r'child', child_viewset, basename='child')

    urlpatterns = [
        re_path(r'^', include(router.urls)),
        re_path(r'^', include(root_router.urls)),
    ]
    return generate_schema(None, patterns=urlpatterns)


@pytest.mark.contrib('drf_nested_routers')
@pytest.mark.parametrize('coerce_suffix,transforms', [
    (False, []),
    (True, [lambda x: x.replace('parent_pk', 'parent_id')]),
])
def test_drf_nested_routers_basic_example(no_warnings, coerce_suffix, transforms):
    class RootViewSet(viewsets.ModelViewSet):
        serializer_class = RootSerializer
        queryset = Root.objects.all()

    class ChildViewSet(viewsets.ModelViewSet):
        serializer_class = ChildSerializer
        queryset = Child.objects.all()

    with mock.patch(
            'drf_spectacular.settings.spectacular_settings.SCHEMA_COERCE_PATH_PK_SUFFIX',
            coerce_suffix
    ):
        assert_schema(
            _generate_nested_routers_schema(RootViewSet, ChildViewSet),
            'tests/contrib/test_drf_nested_routers.yml',
            reverse_transforms=transforms
        )


@pytest.mark.contrib('rest_framework_nested')
def test_drf_nested_routers_basic_example_variation(no_warnings):
    class RootViewSet(viewsets.ModelViewSet):
        queryset = Root.objects.all()
        serializer_class = RootSerializer
        lookup_value_regex = "[0-9]+"

    class ChildViewSet(viewsets.ModelViewSet):
        serializer_class = ChildSerializer

        def get_queryset(self):
            return Child.objects.filter(id=self.kwargs.get("parent_pk"))

    assert_schema(
        _generate_nested_routers_schema(RootViewSet, ChildViewSet),
        'tests/contrib/test_drf_nested_routers.yml',
        reverse_transforms=[
            lambda x: x.replace('format: uuid', 'pattern: ^[0-9]+$'),
            lambda x: x.replace('\n        description: A UUID string identifying this root.', '')
        ]
    )
