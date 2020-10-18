from unittest import mock

import pytest
from rest_framework import mixins, serializers, viewsets

try:
    from rest_framework_gis.fields import GeometryField, GeometrySerializerMethodField
except ImportError:
    GeometryField = object
    GeometrySerializerMethodField = object

from tests import assert_schema, generate_schema


class XSerializer(serializers.Serializer):
    location_method_field = GeometrySerializerMethodField()
    location_field = GeometryField()


class XViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = XSerializer


@pytest.mark.contrib('rest_framework_gis')
@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_OVERRIDES', {})
def test_rest_framework_gis(no_warnings, clear_caches):
    assert_schema(
        generate_schema('x', XViewset),
        'tests/contrib/test_rest_framework_gis.yml'
    )
