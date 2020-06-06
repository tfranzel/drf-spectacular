import uuid

import pytest
from django.db import models
from rest_framework import mixins, serializers, viewsets
from rest_framework.renderers import JSONRenderer

from tests import assert_schema, generate_schema


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


def test_recursion(no_warnings):
    assert_schema(
        generate_schema('nodes', TreeNodeViewset),
        'tests/test_recursion.yml'
    )


@pytest.mark.django_db
def test_model_setup_is_valid():
    root = TreeNode(label='root')
    root.save()
    leaf1 = TreeNode(label='leaf1', parent=root)
    leaf1.save()
    leaf2 = TreeNode(label='leaf2', parent=root)
    leaf2.save()

    JSONRenderer().render(
        TreeNodeSerializer(root).data,
        accepted_media_type='application/json; indent=4'
    ).decode()
