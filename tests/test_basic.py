import uuid
from typing import Optional

from django.db import models
from rest_framework import serializers, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from tests import assert_schema, generate_schema


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
        return True  # pragma: no cover


class AlbumSerializer(serializers.ModelSerializer):
    songs = SongSerializer(many=True, read_only=True)
    single = SongSerializer(read_only=True)

    class Meta:
        fields = '__all__'
        model = Album


class LikeSerializer(serializers.Serializer):
    def save(self, *args, **kwargs):
        pass  # pragma: no cover


class AlbumModelViewset(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = AlbumSerializer
    queryset = Album.objects.none()

    @action(detail=True, methods=['POST'], serializer_class=LikeSerializer)
    def like(self, request):
        return Response(self.get_serializer().data)  # pragma: no cover

    def create(self, request, *args, **kwargs):
        """
        Special documentation about creating albums

        There is even more info here
        """
        return super().create(request, *args, **kwargs)  # pragma: no cover


def test_basic(no_warnings):
    assert_schema(
        generate_schema('albums', AlbumModelViewset),
        'tests/test_basic.yml'
    )
