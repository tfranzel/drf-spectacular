from drf_spectacular.serializers import OpenApiSerializerExtension


class PolymorphicSerializerExtension(OpenApiSerializerExtension):
    target_class = 'rest_polymorphic.serializers.PolymorphicSerializer'
    match_subclasses = True

    def map_serializer(self, auto_schema, method: str):
        sub_components = []
        serializer = self.target

        for sub_model in serializer.model_serializer_mapping:
            sub_serializer = serializer._get_serializer_from_model_or_instance(sub_model)
            resource_type = serializer.to_resource_type(sub_model)
            ref = auto_schema.resolve_serializer(method, sub_serializer).ref
            sub_components.append((resource_type, ref))

        return {
            'oneOf': [ref for _, ref in sub_components],
            'discriminator': {
                'propertyName': serializer.resource_type_field_name,
                'mapping': {resource_type: ref['$ref'] for resource_type, ref in sub_components},
            }
        }
