from abc import abstractmethod
from typing import Optional, List

from drf_spectacular.plumbing import warn, force_instance, OpenApiGeneratorExtension


class OpenApiSerializerExtension(OpenApiGeneratorExtension['OpenApiSerializerExtension']):
    _registry: List['OpenApiSerializerExtension'] = []

    def get_name(self) -> Optional[str]:
        """ return str for overriding default name extraction """
        return None

    @abstractmethod
    def map_serializer(self, auto_schema, method: str):
        pass


class PolymorphicProxySerializerExtension(OpenApiSerializerExtension):
    target_class = 'drf_spectacular.utils.PolymorphicProxySerializer'

    def get_name(self):
        return self.target.component_name

    def map_serializer(self, auto_schema, method: str):
        """ custom handling for @extend_schema's injection of PolymorphicProxySerializer """
        serializer = self.target
        sub_components = []

        for sub_serializer in serializer.serializers:
            sub_serializer = force_instance(sub_serializer)
            sub_components.append(auto_schema.resolve_serializer(method, sub_serializer))

            if serializer.resource_type_field_name not in sub_serializer.fields:
                warn(
                    f'sub-serializer of {serializer.component_name} must have the specified '
                    f'discriminator field "{serializer.resource_type_field_name}".'
                )

        return {
            'oneOf': [c.ref for c in sub_components],
            'discriminator': {
                'propertyName': serializer.resource_type_field_name,
                'mapping': {c.name: c.ref['$ref'] for c in sub_components}
            }
        }
