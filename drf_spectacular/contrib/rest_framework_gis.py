from rest_framework import serializers

from drf_spectacular.extensions import OpenApiSerializerExtension


class GuttedAutoSchemaMeta(type):
    def mro(cls):
        """
        Strip away all base classes related to DRF's AutoSchema. Required methods need to be
        provided by Mixins. This prevents accidental calls into DRF's original AutoSchema.
        Resulting MRO is [GuttedAutoSchemaMeta, USER_AUTOSCHEMA, [Mixins,] Object]
        """
        from rest_framework.schemas.openapi import ViewInspector
        mro = super().mro()
        return mro[:2] + [c for c in mro if not issubclass(c, ViewInspector)]


class GeoFeatureModelSerializerExtension(OpenApiSerializerExtension):
    target_class = 'rest_framework_gis.serializers.GeoFeatureModelSerializer'
    match_subclasses = True

    def map_serializer(self, auto_schema, direction):
        from rest_framework_gis.schema import GeoFeatureAutoSchema

        # hide unknown field warning as GIS fields are resolved to generic ModelField
        PatchedSerializer = type(
            'PatchedSerializer',
            (self.target.__class__, ),
            {self.target.Meta.geo_field: serializers.CharField()}
        )
        # generate schema that serves as foundation to GeoFeatureAutoSchema's modifications
        spectacular_schema = auto_schema._map_serializer(
            PatchedSerializer, direction, bypass_extensions=True
        )

        class Mixin:
            def map_serializer(self, serializer):
                return spectacular_schema

        class PatchedGeoFeatureAutoSchema(GeoFeatureAutoSchema, Mixin, metaclass=GuttedAutoSchemaMeta):
            pass

        return PatchedGeoFeatureAutoSchema().map_serializer(self.target)


class GeoFeatureModelListSerializerExtension(OpenApiSerializerExtension):
    target_class = 'rest_framework_gis.serializers.GeoFeatureModelListSerializer'
    match_subclasses = True

    def map_serializer(self, auto_schema, direction):
        # generate schema that serves as foundation to GeoFeatureAutoSchema's modifications
        return auto_schema._map_serializer(
            self.target, direction, bypass_extensions=True
        )
