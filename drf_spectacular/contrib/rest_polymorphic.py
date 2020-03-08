from drf_spectacular.openapi import AutoSchema

try:
    from rest_polymorphic.serializers import PolymorphicSerializer
except ImportError:
    raise RuntimeError('django-rest-polymorphic package required for PolymorphicAutoSchema')


class PolymorphicAutoSchema(AutoSchema):
    """
        Extended AutoSchema to deal with rest_polymorphic native PolymorphicSerializer
    """

    def _map_serializer(self, method, serializer, nested=False):
        if isinstance(serializer, PolymorphicSerializer):
            return self._map_polymorphic_serializer(method, serializer, nested=False)
        else:
            return super()._map_serializer(method, serializer, nested)

    def _map_polymorphic_serializer(self, method, serializer, nested):
        poly_list = []

        for _, sub_serializer in serializer.model_serializer_mapping.items():
            sub_schema = self.resolve_serializer(method, sub_serializer, nested)
            sub_serializer_name = self._get_serializer_name(method, sub_serializer, nested)

            poly_list.append((sub_serializer_name, sub_schema))

        return {
            'oneOf': [ref for _, ref in poly_list],
            'discriminator': {
                'propertyName': serializer.resource_type_field_name,
                'mapping': {name: ref['$ref'] for name, ref in poly_list}
            }
        }
