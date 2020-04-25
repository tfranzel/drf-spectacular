from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.plumbing import build_array_type, build_basic_type

_FLOAT_TYPE = build_basic_type(float)

# Defined in RFC 7946
# https://gist.github.com/codan-telcikt/e1d59ccc9a3af83e083f1a514c84026c

GEOS_GEOMETRY = {
    'type': 'object',
    'properties': {
        'type': {
            'description': 'The type of the geos instance',
            'type': 'string',
            'enum': [
                'Point',
                'LineString',
                'LinearRing',
                'Polygon',
                'MultiPoint',
                'MultiLineString',
                'MultiPolygon',
            ],
        },
        'coordinates': {
            'oneOf': [
                build_array_type(_FLOAT_TYPE),  # Point
                build_array_type(build_array_type(_FLOAT_TYPE)),  # MultiPoint
                build_array_type(build_array_type(build_array_type(_FLOAT_TYPE))),  # MultiLineString
                build_array_type(build_array_type(build_array_type(build_array_type(_FLOAT_TYPE)))),  # MultiPolygon
            ],
        },
    },
    'required': ['type', 'coordinates'],
}

GEOS_GEOMETRY_COLLECTION = {
    'type': 'object',
    'properties': {
        'type': {
            'type': 'string',
            'description': 'The type of the geos instance',
            'enum': ['GeometryCollection'],
        },
        'geometries': build_array_type(GEOS_GEOMETRY),
    },
    'required': ['type', 'geometries'],
}

GEOJSON_FEATURE = {
    'type': 'object',
    'properties': {
        'type': {
            'description': 'The type of the geos instance',
            'type': 'string',
            'enum': ['Feature'],
        },
        'id': {'type': 'integer'},
        'geometry': GEOS_GEOMETRY_COLLECTION,
        'properties': {'type': 'object'}
    },
    'required': ['id', 'type', 'geometry'],
}

GEOJSON_FEATURE_COLLECTION = {
    'type': 'object',
    'properties': {
        'type': {
            'description': 'The type of the geos instance',
            'type': 'string',
            'enum': ['Feature'],
        },
        'id': {'type': 'integer'},
        'features': build_array_type(GEOJSON_FEATURE),
    },
    'required': ['id', 'type', 'features'],
}


class GeometryFieldExtension(OpenApiSerializerFieldExtension):
    target_class = 'rest_framework_gis.fields.GeometryField'

    def map_serializer_field(self, auto_schema, direction):
        return {
            'oneOf': [
                GEOS_GEOMETRY,
                GEOS_GEOMETRY_COLLECTION,
            ],
        }


class GeometrySerializerMethodFieldExtension(OpenApiSerializerFieldExtension):
    target_class = 'rest_framework_gis.fields.GeometrySerializerMethodField'

    def map_serializer_field(self, auto_schema, direction):
        return {
            'oneOf': [
                GEOJSON_FEATURE,
                GEOJSON_FEATURE_COLLECTION,
            ],
        }
