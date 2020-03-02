from unittest import mock

from django.db import models
from rest_framework import serializers, viewsets, routers

from drf_spectacular.openapi import SchemaGenerator, AutoSchema
from drf_spectacular.renderers import NoAliasOpenAPIRenderer


class Album(models.Model):
    id = models.UUIDField()
    title = models.CharField(max_length=10)
    genre = models.CharField(
        choices=(('POP', 'Pop'), ('ROCK', 'Rock')),
        max_length=10
    )
    year = models.IntegerField()
    released = models.BooleanField()


class Song(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    length = models.IntegerField()


class SongSerializer(serializers.ModelSerializer):
    top10 = serializers.SerializerMethodField()

    class Meta:
        fields = ['id', 'length', 'top10']
        model = Song

    def get_top10(self) -> bool:
        return True


class AlbumSerializer(serializers.ModelSerializer):
    songs = SongSerializer()

    class Meta:
        fields = '__all__'
        model = Album


class AlbumModelViewset(viewsets.ModelViewSet):
    serializer_class = AlbumSerializer


@mock.patch('rest_framework.settings.api_settings.DEFAULT_SCHEMA_CLASS', AutoSchema)
def test_basics():
    router = routers.SimpleRouter()
    router.register('albums', AlbumModelViewset, basename="album")
    generator = SchemaGenerator(patterns=router.urls)
    schema = generator.get_schema(request=None, public=True)
    schema_yml = NoAliasOpenAPIRenderer().render(schema, renderer_context={})

    with open('tests/test_basic.yml') as fh:
        assert schema_yml.decode() == fh.read()
