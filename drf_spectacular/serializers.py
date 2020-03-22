from abc import ABC, abstractmethod
from typing import List, Type, Optional

from django.utils.module_loading import import_string

from drf_spectacular.plumbing import warn, force_instance


class OpenApiSerializerExtension(ABC):
    _registry: List[Type['OpenApiSerializerExtension']] = []

    serializer_class = None
    name: str

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._registry.append(cls)

    @classmethod
    def _matches(cls, serializer) -> bool:
        if isinstance(cls.serializer_class, str):
            try:
                cls.serializer_class = import_string(cls.serializer_class)
            except ImportError:
                cls.serializer_class = None

        if cls.serializer_class is None:
            return False  # app not installed
        else:
            return issubclass(serializer.__class__, cls.serializer_class)

    @classmethod
    def get_match(cls, serializer) -> Optional[Type['OpenApiSerializerExtension']]:
        for scheme in cls._registry:
            if scheme._matches(serializer):
                return scheme
        return None

    @classmethod
    @abstractmethod
    def map_serializer(cls, auto_schema, method: str, serializer):
        pass


class PolymorphicProxySerializerExtension(OpenApiSerializerExtension):
    serializer_class = 'drf_spectacular.utils.PolymorphicProxySerializer'

    @classmethod
    def map_serializer(cls, auto_schema, method: str, serializer):
        """ custom handling for @extend_schema's injection of PolymorphicProxySerializer """
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
