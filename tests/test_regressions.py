from unittest import mock

from django.db import models
from rest_framework import serializers, viewsets, mixins

from drf_spectacular.openapi import AutoSchema
from tests import generate_schema


@mock.patch('rest_framework.settings.api_settings.DEFAULT_SCHEMA_CLASS', AutoSchema)
def test_primary_key_read_only_queryset_not_found(no_warnings):
    # the culprit - looks like a feature not a bug.
    # https://github.com/encode/django-rest-framework/blame/4d9f9eb192c5c1ffe4fa9210b90b9adbb00c3fdd/rest_framework/utils/field_mapping.py#L271

    class M1(models.Model):
        pass

    class M2(models.Model):
        m1_r = models.ForeignKey(M1, on_delete=models.CASCADE)
        m1_rw = models.ForeignKey(M1, on_delete=models.CASCADE)

    class M2Serializer(serializers.ModelSerializer):
        class Meta:
            fields = ['m1_rw', 'm1_r']
            read_only_fields = ['m1_r']  # this produces the bug
            model = M2

    class M2Viewset(viewsets.ReadOnlyModelViewSet):
        serializer_class = M2Serializer
        queryset = M2.objects.none()

    schema = generate_schema('m2', M2Viewset)
    props = schema['components']['schemas']['M2']['properties']
    assert props['m1_rw']['type'] == 'integer'
    assert props['m1_r']['type'] == 'integer'


@mock.patch('rest_framework.settings.api_settings.DEFAULT_SCHEMA_CLASS', AutoSchema)
def test_serializer_name_reuse(warnings):
    from rest_framework import routers
    from drf_spectacular.openapi import SchemaGenerator
    router = routers.SimpleRouter()

    def x1():
        class XSerializer(serializers.Serializer):
            uuid = serializers.UUIDField()

        return XSerializer

    def x2():
        class XSerializer(serializers.Serializer):
            integer = serializers.IntegerField

        return XSerializer

    class X1Viewset(mixins.ListModelMixin, viewsets.GenericViewSet):
        serializer_class = x1()

    router.register('x1', X1Viewset, basename='x1')

    class X2Viewset(mixins.ListModelMixin, viewsets.GenericViewSet):
        serializer_class = x2()

    router.register('x2', X2Viewset, basename='x2')

    generator = SchemaGenerator(patterns=router.urls)
    generator.get_schema(request=None, public=True)
