from abc import abstractmethod
from typing import List

from drf_spectacular.plumbing import OpenApiGeneratorExtension


class OpenApiSerializerFieldExtension(OpenApiGeneratorExtension['OpenApiSerializerFieldExtension']):
    _registry: List['OpenApiSerializerExtension'] = []

    @abstractmethod
    def map_serializer_field(self, auto_schema):
        pass
