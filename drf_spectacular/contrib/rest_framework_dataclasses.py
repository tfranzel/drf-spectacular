from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.plumbing import get_doc
from drf_spectacular.utils import Direction


class OpenApiDataclassSerializerExtensions(OpenApiSerializerExtension):
    target_class = "rest_framework_dataclasses.serializers.DataclassSerializer"
    match_subclasses = True

    def get_name(self):
        """Use the dataclass name in the schema, instead of the serializer prefix (which can be just Dataclass)."""
        return self.target.dataclass_definition.dataclass_type.__name__

    def strip_library_doc(self, schema):
        """Strip the DataclassSerializer library documentation from the schema."""
        from rest_framework_dataclasses.serializers import DataclassSerializer
        if 'description' in schema and schema['description'] == get_doc(DataclassSerializer):
            del schema['description']
        return schema

    def map_serializer(self, auto_schema, direction: Direction):
        """"Generate the schema for a DataclassSerializer."""
        schema = auto_schema._map_serializer(self.target, direction, bypass_extensions=True)
        return self.strip_library_doc(schema)
