from unittest import mock

import pytest
from django.db import models
from rest_framework import mixins, viewsets

try:
    from django.contrib.gis.db.models import PolygonField
    from rest_framework_gis.fields import GeometryField, GeometrySerializerMethodField
    # from django.contrib.gis.db.models import GeometryField as DbGeometryField, PointField, PolygonField
    from rest_framework_gis.serializers import GeoFeatureModelSerializer
except ImportError:
    GeometryField = object
    GeometrySerializerMethodField = object
    GeoFeatureModelSerializer = object

from tests import assert_schema, generate_schema


class Location(models.Model):
    point = PolygonField()


class SchemaBaseModel(models.Model):
    random_field1 = models.CharField(max_length=32)
    random_field2 = models.IntegerField()

    class Meta:
        abstract = True


class GeoModel(SchemaBaseModel):
    location = PolygonField()


class PointSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = GeoModel
        geo_field = 'location'
        fields = '__all__'


# class LocationSerializer(GeoFeatureModelSerializer):
#     """ A class to serialize locations as GeoJSON compatible data """
#
#     # a field which contains a geometry value and can be used as geo_field
#     other_point = GeometrySerializerMethodField()
#
#     def get_other_point(self, obj):
#         return Point(obj.point.lat / 2, obj.point.lon / 2)
#
#     class Meta:
#         model = Location
#         geo_field = 'other_point'
#         fields = '__all__'

#
# class XSerializer(serializers.Serializer):
#     location_method_field = GeometrySerializerMethodField()
#     location_field = GeometryField()


class XViewset(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = PointSerializer
    queryset = GeoModel.objects.none()


@pytest.mark.contrib('rest_framework_gis')
@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_OVERRIDES', {})
def test_rest_framework_gis(no_warnings, clear_caches):
    assert_schema(
        generate_schema('x', XViewset),
        'tests/contrib/test_rest_framework_gis.yml'
    )
