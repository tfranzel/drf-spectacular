from drf_spectacular.serializers import OpenApiSerializerExtension


class PolymorphicSerializerExtension(OpenApiSerializerExtension):
    serializer_class = 'rest_polymorphic.serializers.PolymorphicSerializer'

    @classmethod
    def map_serializer(cls, auto_schema, method: str, serializer):
        sub_components = []

        for _, sub_serializer in serializer.model_serializer_mapping.items():
            sub_components.append(auto_schema.resolve_serializer(method, sub_serializer))

        return {
            'oneOf': [c.ref for c in sub_components],
            'discriminator': {
                'propertyName': serializer.resource_type_field_name,
                'mapping': {c.name: c.ref['$ref'] for c in sub_components},
            }
        }
