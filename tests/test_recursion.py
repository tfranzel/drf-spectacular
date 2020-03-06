import uuid
from unittest import mock

from django.db import models
from rest_framework import serializers, viewsets, routers, mixins

from drf_spectacular.openapi import SchemaGenerator, AutoSchema
from drf_spectacular.renderers import NoAliasOpenAPIRenderer


class TreeNode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    label = models.TextField()

    parent = models.ForeignKey(
        'TreeNode',
        null=True,
        blank=True,
        related_name='children',
        on_delete=models.DO_NOTHING
    )


class TreeNodeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'label', 'parent', 'children']
        model = TreeNode

    def get_fields(self):
        fields = super(TreeNodeSerializer, self).get_fields()
        fields['children'] = TreeNodeSerializer(many=True)
        return fields


class TreeNodeViewset(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = TreeNodeSerializer
    queryset = TreeNode.objects.none()


@mock.patch('rest_framework.settings.api_settings.DEFAULT_SCHEMA_CLASS', AutoSchema)
def test_recursion():
    router = routers.SimpleRouter()
    router.register('nodes', TreeNodeViewset, basename="nodes")
    generator = SchemaGenerator(patterns=router.urls)
    schema = generator.get_schema(request=None, public=True)
    schema_yml = NoAliasOpenAPIRenderer().render(schema, renderer_context={})

    with open('tests/test_recursion.yml') as fh:
        assert schema_yml.decode() == fh.read()
