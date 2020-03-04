import uuid
from unittest import mock

from django.db import models
from rest_framework import serializers, viewsets, routers

from drf_spectacular.openapi import SchemaGenerator, AutoSchema
from drf_spectacular.renderers import NoAliasOpenAPIRenderer


class Album(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    genre = models.CharField(
        choices=(('POP', 'Pop'), ('ROCK', 'Rock')),
        max_length=10
    )
    year = models.IntegerField()
    released = models.BooleanField()


class Song(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    album = models.ForeignKey(Album, on_delete=models.CASCADE)

    title = models.CharField(max_length=100)
    length = models.IntegerField()


class SongSerializer(serializers.ModelSerializer):
    top10 = serializers.SerializerMethodField()

    class Meta:
        fields = ['id', 'title', 'length', 'top10']
        model = Song

    def get_top10(self) -> bool:
        return True


class AlbumSerializer(serializers.ModelSerializer):
    songs = SongSerializer(many=True, read_only=True)

    class Meta:
        fields = '__all__'
        model = Album


class AlbumModelViewset(viewsets.ModelViewSet):
    serializer_class = AlbumSerializer
    queryset = Album.objects.none()

    def create(self, request, *args, **kwargs):
        """
        Special documentation about creating albums

        There is even more info here
        """
        return super().create(request, *args, **kwargs)


@mock.patch('rest_framework.settings.api_settings.DEFAULT_SCHEMA_CLASS', AutoSchema)
def test_basics():
    router = routers.SimpleRouter()
    router.register('albums', AlbumModelViewset, basename="album")
    generator = SchemaGenerator(patterns=router.urls)
    schema = generator.get_schema(request=None, public=True)
    schema_yml = NoAliasOpenAPIRenderer().render(schema, renderer_context={})

    with open('tests/test_basic.yml') as fh:
        assert schema_yml.decode() == fh.read()
