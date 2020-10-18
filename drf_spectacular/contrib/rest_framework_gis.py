from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.plumbing import ResolvedComponent, build_array_type, build_basic_type

# Defined in RFC 7946
# https://gist.github.com/codan-telcikt/e1d59ccc9a3af83e083f1a514c84026c


def build_component(registry, name, schema):
    component = ResolvedComponent(
        name=name,
        type=ResolvedComponent.SCHEMA,
        schema=schema,
        object=name,
    )
    registry.register_on_missing(component)
    return component


def get_point(registry):
    schema = {
        **build_array_type(build_basic_type(float)),
        'minItems': 2,
        'maxItems': 3,
    }
    return build_component(registry, 'GisPoint', schema)


def get_geos_geometry(registry):
    point = get_point(registry)
    schema = {
        'type': 'object',
        'properties': {
            'type': {
                'type': 'string',
                'description': 'The type of the geos instance',
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
                    point.ref,  # Point
                    build_array_type(point.ref),  # MultiPoint, LineString
                    build_array_type(build_array_type(point.ref)),  # MultiLineString, Polygon
                    build_array_type(build_array_type(build_array_type(point.ref))),  # MultiPolygon
                ],
            },
        },
        'required': ['type', 'coordinates'],
    }
    return build_component(registry, 'GisGeometry', schema)


def get_geos_geometry_collection(registry):
    geos_geometry = get_geos_geometry(registry)
    schema = {
        'type': 'object',
        'properties': {
            'type': {
                'type': 'string',
                'description': 'The type of the geos instance',
                'enum': ['GeometryCollection'],
            },
            'geometries': build_array_type(geos_geometry.ref),
        },
        'required': ['type', 'geometries'],
    }
    return build_component(registry, 'GisGeometryCollection', schema)


def get_geojson_feature(registry):
    geos_geometry_collection = get_geos_geometry_collection(registry)
    schema = {
        'type': 'object',
        'properties': {
            'type': {
                'type': 'string',
                'description': 'The type of the geos instance',
                'enum': ['Feature'],
            },
            'id': {'type': 'integer'},
            'geometry': geos_geometry_collection.ref,
            'properties': {'type': 'object'}
        },
        'required': ['id', 'type', 'geometry'],
    }
    return build_component(registry, 'GisFeature', schema)


def get_geojson_feature_collection(registry):
    geojson_feature = get_geojson_feature(registry)
    schema = {
        'type': 'object',
        'properties': {
            'type': {
                'type': 'string',
                'description': 'The type of the geos instance',
                'enum': ['Feature'],
            },
            'id': {'type': 'integer'},
            'features': build_array_type(geojson_feature.ref),
        },
        'required': ['id', 'type', 'features'],
    }
    return build_component(registry, 'GisFeatureCollection', schema)


def _inject_enum_collision_fix():
    from drf_spectacular.settings import spectacular_settings
    if 'GisFeatureEnum' not in spectacular_settings.ENUM_NAME_OVERRIDES:
        spectacular_settings.ENUM_NAME_OVERRIDES['GisFeatureEnum'] = ('Feature',)


class GeometryFieldExtension(OpenApiSerializerFieldExtension):
    target_class = 'rest_framework_gis.fields.GeometryField'

    def map_serializer_field(self, auto_schema, direction):
        _inject_enum_collision_fix()
        return {
            'oneOf': [
                get_geos_geometry(auto_schema.registry).ref,
                get_geos_geometry_collection(auto_schema.registry).ref,
            ],
        }


class GeometrySerializerMethodFieldExtension(OpenApiSerializerFieldExtension):
    target_class = 'rest_framework_gis.fields.GeometrySerializerMethodField'

    def map_serializer_field(self, auto_schema, direction):
        _inject_enum_collision_fix()
        return {
            'oneOf': [
                get_geojson_feature(auto_schema.registry).ref,
                get_geojson_feature_collection(auto_schema.registry).ref,
            ],
        }
