import uuid
from typing import Optional

from django.db import models
from rest_framework import serializers, viewsets, routers
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response

from drf_spectacular.openapi import SchemaGenerator
from tests import assert_schema


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

    def get_top10(self) -> Optional[bool]:
        return True


class AlbumSerializer(serializers.ModelSerializer):
    songs = SongSerializer(many=True, read_only=True)
    single = SongSerializer(read_only=True)

    class Meta:
        fields = '__all__'
        model = Album


class LikeSerializer(serializers.Serializer):
    def save(self, *args, **kwargs):
        pass  # do the liking


class AlbumModelViewset(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    serializer_class = AlbumSerializer
    queryset = Album.objects.none()

    @action(detail=True, methods=['POST'], serializer_class=LikeSerializer)
    def like(self, request):
        return Response(self.get_serializer().data)

    def create(self, request, *args, **kwargs):
        """
        Special documentation about creating albums

        There is even more info here
        """
        return super().create(request, *args, **kwargs)


def test_basics(no_warnings):
    router = routers.SimpleRouter()
    router.register('albums', AlbumModelViewset, basename="album")
    generator = SchemaGenerator(patterns=router.urls)
    schema = generator.get_schema(request=None, public=True)

    assert_schema(schema, 'tests/test_basic.yml')
