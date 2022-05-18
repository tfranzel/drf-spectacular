from django.contrib.gis.db.models import GeometryCollectionField, GeometryField
from django.db.models import Model
from rest_framework.fields import Field
from rest_framework_gis.schema import GeoFeatureAutoSchema

from drf_spectacular.extensions import (
    OpenApiSerializerExtension,
    OpenApiSerializerFieldExtension,
)
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import (
    build_basic_type,
    follow_field_source,
    get_view_model,
)
from drf_spectacular.types import OpenApiTypes


class GeometryFieldExtension(OpenApiSerializerFieldExtension):

    target_class = "rest_framework_gis.fields.GeometryField"
    match_subclasses = True

    def _get_model_field(self, filter_field: Field, model: Model):
        if not filter_field.field_name:
            return None
        path = filter_field.field_name.split("__")
        return follow_field_source(model, path, emit_warnings=False)

    def map_serializer_field(
        self, auto_schema: AutoSchema, direction: str
    ) -> dict:
        if direction is None:
            # direction = None means this is being called for a filter
            # field, so format should be WKT rather than GeoJSON
            return build_basic_type(OpenApiTypes.STR)

        # Try a few different ways to figure out the underlying model class
        try:
            model = auto_schema.view.get_serializer_class().Meta.model
        except AttributeError:
            try:
                model = auto_schema.view.serializer_class.Meta.model
            except AttributeError:
                model = get_view_model(auto_schema.view)

        if model is not None:
            model_field = self._get_model_field(self.target, model)
            if model_field.__class__ in [
                GeometryField,
                GeometryCollectionField,
            ]:
                # rest_framework_gis has invalid openapi definitions for these,
                # so just return generic object
                return {"type": "object"}
            schema = GeoFeatureAutoSchema.GEO_FIELD_TO_SCHEMA[
                model_field.__class__
            ]
            return {"type": "object", "properties": schema}
        else:
            # Fallback if the model can't be determined
            return {"type": "object"}


class GeoFeatureModelSerializerExtension(OpenApiSerializerExtension):

    target_class = "rest_framework_gis.serializers.GeoFeatureModelSerializer"
    match_subclasses = True

    # Everything other than these fields should be nested under "properties"
    # rather than being a top-level JSON field.
    TOP_LEVEL_PROPS = ["geometry", "geometries", "crs", "bbox"]

    def map_serializer(self, auto_schema: AutoSchema, direction: str) -> dict:
        schema = auto_schema._map_serializer(
            self.target, direction, bypass_extensions=True
        )
        nested_properties = {}
        nested_required = []
        for property in list(schema["properties"].keys()):
            # list() is called above to copy the dict since this deletes
            # elements while iterating
            if property not in self.TOP_LEVEL_PROPS:
                nested_properties[property] = schema["properties"][property]
                del schema["properties"][property]
                if property in schema["required"]:
                    nested_required.append(property)
                    schema["required"].remove(property)
        schema["properties"]["properties"] = {
            "type": "object",
            "properties": nested_properties,
            "required": nested_required,
        }
        schema["properties"]["type"] = {
            "type": "string",
            "enum": ["Feature"],
        }
        return schema
