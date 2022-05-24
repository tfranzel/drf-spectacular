from unittest import mock

import pytest
from django.db import models
from rest_framework import __version__ as DRF_VERSION  # type: ignore[attr-defined]
from rest_framework import mixins, routers, serializers, viewsets

from drf_spectacular.utils import extend_schema_serializer
from tests import assert_schema, generate_schema


@pytest.mark.contrib('rest_framework_gis')
@pytest.mark.skipif(DRF_VERSION < '3.12', reason='DRF pagination schema broken')
@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_OVERRIDES', {})
def test_rest_framework_gis(no_warnings, clear_caches):
    from django.contrib.gis.db.models import (
        GeometryCollectionField, GeometryField, LineStringField, MultiLineStringField,
        MultiPointField, MultiPolygonField, PointField, PolygonField,
    )
    from rest_framework_gis.pagination import GeoJsonPagination
    from rest_framework_gis.serializers import GeoFeatureModelSerializer

    class GeoModel(models.Model):
        field_random1 = models.CharField(max_length=32)
        field_random2 = models.IntegerField()
        field_gis_plain = PointField()

        field_polygon = PolygonField()
        field_point = PointField()
        field_linestring = LineStringField()
        field_geometry = GeometryField()
        field_multipolygon = MultiPolygonField()
        field_multipoint = MultiPointField()
        field_multilinestring = MultiLineStringField()
        field_geometrycollection = GeometryCollectionField()

    router = routers.SimpleRouter()

    # all GIS fields as GeoJSON in singular and list form
    fields = [
        'Point', 'Polygon', 'Linestring', 'Geometry',
        'Multipoint', 'Multipolygon', 'Multilinestring', 'Geometrycollection'
    ]
    for name in fields:
        @extend_schema_serializer(component_name=name)
        class XSerializer(GeoFeatureModelSerializer):
            class Meta:
                model = GeoModel
                geo_field = f'field_{name.lower()}'
                auto_bbox = name == 'Polygon'
                fields = ['id', 'field_random1', 'field_random2', 'field_gis_plain']

        class XViewset(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
            serializer_class = XSerializer
            queryset = GeoModel.objects.none()

        router.register(name.lower(), XViewset, basename=name)

    # plain serializer with GIS fields but without restructured container object
    class PlainSerializer(serializers.ModelSerializer):
        class Meta:
            model = GeoModel
            fields = ['id', 'field_random1', 'field_random2', 'field_gis_plain']

    class PlainViewset(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
        serializer_class = PlainSerializer
        queryset = GeoModel.objects.none()

    router.register('plain', PlainViewset, basename='plain')

    # GIS specific pagination
    class PlainViewset(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
        serializer_class = PlainSerializer
        queryset = GeoModel.objects.none()
        pagination_class = GeoJsonPagination

    router.register('paginated', PlainViewset, basename='paginated')

    assert_schema(
        generate_schema(None, patterns=router.urls),
        'tests/contrib/test_rest_framework_gis.yml'
    )
