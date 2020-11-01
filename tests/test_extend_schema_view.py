import pytest
from django.db import models
from rest_framework import mixins, routers, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.test import APIClient

from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view
from tests import assert_schema


class ESVModel(models.Model):
    pass


class ESVSerializer(serializers.ModelSerializer):
    class Meta:
        model = ESVModel
        fields = '__all__'


@extend_schema(tags=['global-tag'])
@extend_schema_view(
    list=extend_schema(description='view list description'),
    retrieve=extend_schema(description='view retrieve description'),
    extended_action=extend_schema(description='view extended action description'),
    raw_action=extend_schema(description='view raw action description'),
)
class XViewset(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = ESVModel.objects.all()
    serializer_class = ESVSerializer

    @extend_schema(tags=['custom-retrieve-tag'])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(responses=OpenApiTypes.DATE)
    @action(detail=False)
    def extended_action(self, request):
        return Response('2020-10-31')

    @action(detail=False, methods=['GET'])
    def raw_action(self, request):
        return Response('2019-03-01')


# view to make sure there is no cross-talk
class YViewSet(viewsets.ModelViewSet):
    serializer_class = ESVSerializer
    queryset = ESVModel.objects.all()


router = routers.SimpleRouter()
router.register('x', XViewset)
router.register('y', YViewSet)
urlpatterns = router.urls


@pytest.mark.urls(__name__)
def test_extend_schema_view(no_warnings):
    assert_schema(
        SchemaGenerator().get_schema(request=None, public=True),
        'tests/test_extend_schema_view.yml'
    )


@pytest.mark.urls(__name__)
@pytest.mark.django_db
def test_extend_schema_view_call_transparency(no_warnings):
    ESVModel.objects.create()

    response = APIClient().get('/x/')
    assert response.status_code == 200
    assert response.content == b'[{"id":1}]'
    response = APIClient().get('/x/1/')
    assert response.status_code == 200
    assert response.content == b'{"id":1}'
    response = APIClient().get('/x/extended_action/')
    assert response.status_code == 200
    assert response.content == b'"2020-10-31"'
    response = APIClient().get('/x/raw_action/')
    assert response.status_code == 200
    assert response.content == b'"2019-03-01"'
