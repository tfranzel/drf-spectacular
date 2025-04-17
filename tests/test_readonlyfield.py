import uuid

from django.db import models
from rest_framework import serializers, viewsets

from tests import assert_schema, generate_schema


class Cubicle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class Employee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cubicle = models.ForeignKey(Cubicle, on_delete=models.CASCADE, null=True)


class EmployeeSerializer(serializers.ModelSerializer):

    cubicle_id = serializers.ReadOnlyField(source='cubicle.id')

    class Meta:
        fields = ['id', 'cubicle_id']
        model = Employee


class EmployeeModelViewset(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    queryset = Employee.objects.none()


def test_readonlyfield(no_warnings, django_transforms):
    assert_schema(
        generate_schema('songs', EmployeeModelViewset),
        'tests/test_readonlyfield.yml',
        transforms=django_transforms,
    )
