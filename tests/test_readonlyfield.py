import uuid

from django.db import models
from rest_framework import serializers, viewsets

from tests import assert_schema, generate_schema


class Album(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class Song(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    album = models.ForeignKey(Album, on_delete=models.CASCADE, null=True)


class SongSerializer(serializers.ModelSerializer):

    album_id = serializers.ReadOnlyField(source='album.id')

    class Meta:
        fields = ['id', 'album_id']
        model = Song


class SongModelViewset(viewsets.ModelViewSet):
    serializer_class = SongSerializer
    queryset = Song.objects.none()


def test_readonlyfield(no_warnings, django_transforms):
    assert_schema(
        generate_schema('songs', SongModelViewset),
        'tests/test_readonlyfield.yml',
        transforms=django_transforms,
    )
