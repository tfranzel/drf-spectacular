import re
from unittest import mock

import pytest
from django.db import models
from rest_framework import __version__ as DRF_VERSION  # type: ignore[attr-defined]
from rest_framework import mixins, routers, serializers, viewsets

from drf_spectacular.utils import extend_schema_serializer
from tests import assert_schema, generate_schema, is_gis_installed


@pytest.mark.contrib('rest_framework_gis')
@pytest.mark.system_requirement_fulfilled(is_gis_installed())
@pytest.mark.skipif(DRF_VERSION < '3.12', reason='DRF pagination schema broken')
@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_OVERRIDES', {})
def test_rest_framework_gis(no_warnings, clear_caches, django_transforms):
    from django.contrib.gis.db.models import (
        GeometryCollectionField, GeometryField, LineStringField, MultiLineStringField,
        MultiPointField, MultiPolygonField, PointField, PolygonField,
    )
    from rest_framework_gis.fields import GeometryField as SerializerGeometryField
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

    class GeoModel2(models.Model):
        related_model = models.OneToOneField(GeoModel, on_delete=models.DO_NOTHING)
        field_point = PointField()

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
        field_gis_related = SerializerGeometryField(source="geomodel2.field_point")

        class Meta:
            model = GeoModel
            fields = ['id', 'field_random1', 'field_random2', 'field_gis_plain', 'field_gis_related']

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
        'tests/contrib/test_rest_framework_gis.yml',
        transforms=[
            *django_transforms,
            lambda x: re.sub(r'\s+required:\n\s+- count\n\s+- results', '', x, flags=re.M)
        ],
    )


@pytest.mark.contrib('rest_framework_gis', 'django_filter')
@pytest.mark.system_requirement_fulfilled(is_gis_installed())
@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_OVERRIDES', {})
def test_geo_filter_set(no_warnings):
    from django.contrib.gis.db.models import PointField
    from django_filters import filters
    from django_filters.rest_framework import DjangoFilterBackend
    from rest_framework_gis.filters import GeometryFilter
    from rest_framework_gis.filterset import GeoFilterSet

    class GeoRegionModel(models.Model):
        slug = models.CharField(max_length=32)
        geom = PointField()

    class RegionFilter(GeoFilterSet):
        slug = filters.CharFilter(field_name='slug', lookup_expr='istartswith')
        contains_geom = GeometryFilter(field_name='geom', lookup_expr='contains')

        class Meta:
            model = GeoRegionModel
            fields = ['slug', 'contains_geom']

    class XSerializer(serializers.Serializer):
        slug = serializers.CharField()

    class XViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
        serializer_class = XSerializer
        queryset = GeoRegionModel.objects.none()
        filterset_class = RegionFilter
        filter_backends = [DjangoFilterBackend]

    schema = generate_schema('/x', XViewset)
    assert schema['paths']['/x/']['get']['parameters'] == [
        {'in': 'query', 'name': 'contains_geom', 'schema': {'type': 'string'}},
        {'in': 'query', 'name': 'slug', 'schema': {'type': 'string'}}
    ]
