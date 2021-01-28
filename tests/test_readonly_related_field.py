from django.db import models
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from tests import assert_schema, generate_schema


class ReferencedModel(models.Model):
    id = models.AutoField(primary_key=True)


class ReferencingModel(models.Model):
    id = models.UUIDField(primary_key=True)
    referenced_model = models.ForeignKey(ReferencedModel, on_delete=models.CASCADE)
    referenced_model_readonly = models.ForeignKey(ReferencedModel, on_delete=models.CASCADE)
    referenced_model_m2m = models.ManyToManyField(ReferencedModel)
    referenced_model_m2m_readonly = models.ManyToManyField(ReferencedModel)


class ReferencingModelSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ['id', 'referenced_model', 'referenced_model_readonly',
                  'referenced_model_m2m', 'referenced_model_m2m_readonly']
        read_only_fields = ['id', 'referenced_model_readonly', 'referenced_model_m2m_readonly']
        model = ReferencingModel


class ReferencingModelViewset(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = ReferencingModelSerializer
    queryset = ReferencingModel.objects.all()


def test_readonly_related_field(no_warnings):
    assert_schema(
        generate_schema('referencing_model', ReferencingModelViewset),
        'tests/test_readonly_related_field.yml'
    )
