from django.db import models
from rest_framework import serializers


class SimpleModel(models.Model):
    pass


class SimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimpleModel
        fields = '__all__'
