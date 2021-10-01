from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.plumbing import warn


class PolymorphicSerializerExtension(OpenApiSerializerExtension):
    target_class = 'rest_polymorphic.serializers.PolymorphicSerializer'
    match_subclasses = True

    def map_serializer(self, auto_schema, direction):
        sub_components = []
        serializer = self.target

        for sub_model in serializer.model_serializer_mapping:
            sub_serializer = serializer._get_serializer_from_model_or_instance(sub_model)
            sub_serializer.partial = serializer.partial
            resource_type = serializer.to_resource_type(sub_model)
            component = auto_schema.resolve_serializer(sub_serializer, direction)
            if not component:
                continue
            sub_components.append((resource_type, component.ref))

            if not resource_type:
                warn(
                    f'discriminator mapping key is empty for {sub_serializer.__class__}. '
                    f'this might lead to code generation issues.'
                )

        return {
            'oneOf': [ref for _, ref in sub_components],
            'discriminator': {
                'propertyName': serializer.resource_type_field_name,
                'mapping': {resource_type: ref['$ref'] for resource_type, ref in sub_components},
            }
        }
