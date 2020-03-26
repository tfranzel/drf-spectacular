from drf_spectacular.serializers import OpenApiSerializerExtension


class PolymorphicSerializerExtension(OpenApiSerializerExtension):
    target_class = 'rest_polymorphic.serializers.PolymorphicSerializer'
    match_subclasses = True

    def map_serializer(self, auto_schema, method: str):
        sub_components = []
        serializer = self.target

        for _, sub_serializer in serializer.model_serializer_mapping.items():
            sub_components.append(auto_schema.resolve_serializer(method, sub_serializer))

        return {
            'oneOf': [c.ref for c in sub_components],
            'discriminator': {
                'propertyName': serializer.resource_type_field_name,
                'mapping': {c.name: c.ref['$ref'] for c in sub_components},
            }
        }
