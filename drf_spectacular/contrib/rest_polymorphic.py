from drf_spectacular.openapi import AutoSchema

try:
    from rest_polymorphic.serializers import PolymorphicSerializer
except ImportError:
    raise RuntimeError('django-rest-polymorphic package required for PolymorphicAutoSchema')


class PolymorphicAutoSchema(AutoSchema):
    """
        Extended AutoSchema to deal with rest_polymorphic native PolymorphicSerializer
    """

    def _map_serializer(self, method, serializer):
        if isinstance(serializer, PolymorphicSerializer):
            return self._map_polymorphic_serializer(method, serializer)
        else:
            return super()._map_serializer(method, serializer)

    def _map_polymorphic_serializer(self, method, serializer):
        sub_components = []

        for _, sub_serializer in serializer.model_serializer_mapping.items():
            sub_components.append(self.resolve_serializer(method, sub_serializer))

        return {
            'oneOf': [c.ref for c in sub_components],
            'discriminator': {
                'propertyName': serializer.resource_type_field_name,
                'mapping': {c.name: c.ref['$ref'] for c in sub_components},
            }
        }
