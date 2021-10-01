from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.plumbing import force_instance, warn


class PolymorphicProxySerializerExtension(OpenApiSerializerExtension):
    target_class = 'drf_spectacular.utils.PolymorphicProxySerializer'
    priority = -1

    def get_name(self):
        return self.target.component_name

    def map_serializer(self, auto_schema, direction):
        """ custom handling for @extend_schema's injection of PolymorphicProxySerializer """
        if isinstance(self.target.serializers, dict):
            sub_components = self._get_explicit_sub_components(auto_schema, direction)
        else:
            sub_components = self._get_implicit_sub_components(auto_schema, direction)

        if self.target.resource_type_field_name is None:
            return {'oneOf': [ref for _, ref in sub_components]}
        else:
            return {
                'oneOf': [ref for _, ref in sub_components],
                'discriminator': {
                    'propertyName': self.target.resource_type_field_name,
                    'mapping': {resource_type: ref['$ref'] for resource_type, ref in sub_components}
                }
            }

    def _get_implicit_sub_components(self, auto_schema, direction):
        sub_components = []
        for sub_serializer in self.target.serializers:
            sub_serializer = force_instance(sub_serializer)
            sub_serializer.partial = self.target.partial
            resolved_sub_serializer = auto_schema.resolve_serializer(sub_serializer, direction)
            if not resolved_sub_serializer:
                continue

            try:
                discriminator_field = sub_serializer.fields[self.target.resource_type_field_name]
                resource_type = discriminator_field.to_representation(None)
            except:  # noqa: E722
                if self.target.resource_type_field_name is not None:
                    warn(
                        f'sub-serializer {resolved_sub_serializer.name} of {self.target.component_name} '
                        f'must contain the discriminator field "{self.target.resource_type_field_name}". '
                        f'defaulting to sub-serializer name, but schema will likely not match the API.'
                    )
                resource_type = resolved_sub_serializer.name

            sub_components.append((resource_type, resolved_sub_serializer.ref))

        return sub_components

    def _get_explicit_sub_components(self, auto_schema, direction):
        sub_components = []
        for resource_type, sub_serializer in self.target.serializers.items():
            sub_serializer = force_instance(sub_serializer)
            sub_serializer.partial = self.target.partial
            resolved_sub_serializer = auto_schema.resolve_serializer(sub_serializer, direction)
            if not resolved_sub_serializer:
                continue
            sub_components.append((resource_type, resolved_sub_serializer.ref))

        return sub_components
