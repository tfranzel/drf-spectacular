import warnings

from drf_spectacular.openapi import AutoSchema

try:
    from rest_polymorphic.serializers import PolymorphicSerializer
except ImportError:
    warnings.warn('rest_polymorphic package required for PolymorphicAutoSchema')
    raise


class PolymorphicAutoSchema(AutoSchema):
    """
        Extended AutoSchema to deal with rest_polymorphic native PolymorphicSerializer
    """

    def resolve_serializer(self, method, serializer, nested=False):
        if isinstance(serializer, PolymorphicSerializer):
            return self._resolve_polymorphic_serializer(method, serializer, nested)
        else:
            return super().resolve_serializer(method, serializer, nested)

    def _resolve_polymorphic_serializer(self, method, serializer, nested):
        polymorphic_names = []

        for poly_model, poly_serializer in serializer.model_serializer_mapping.items():
            name = self._get_serializer_name(method, poly_serializer, nested)

            if name not in self.registry.schemas:
                # add placeholder to prevent recursion loop
                self.registry.schemas[name] = None
                # append the type field to serializer fields
                mapped = self._map_serializer(method, poly_serializer, nested)
                mapped['properties'][serializer.resource_type_field_name] = {'type': 'string'}
                self.registry.schemas[name] = mapped

            polymorphic_names.append(name)

        return {
            'oneOf': [
                {'$ref': '#/components/schemas/{}'.format(name)} for name in polymorphic_names
            ],
            'discriminator': {
                'propertyName': serializer.resource_type_field_name
            }
        }
