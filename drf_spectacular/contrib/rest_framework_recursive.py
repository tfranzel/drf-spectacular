from drf_spectacular.extensions import OpenApiSerializerFieldExtension


class RecursiveFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "rest_framework_recursive.fields.RecursiveField"

    def map_serializer_field(self, auto_schema, direction):
        component = auto_schema.resolve_serializer(self.target.proxied, direction)
        return component.ref
