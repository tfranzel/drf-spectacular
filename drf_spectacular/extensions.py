from abc import abstractmethod
from typing import List, Optional

from drf_spectacular.plumbing import OpenApiGeneratorExtension


class OpenApiAuthenticationExtension(OpenApiGeneratorExtension['OpenApiAuthenticationExtension']):
    """

    """
    _registry: List['OpenApiAuthenticationExtension'] = []

    name: str

    def get_security_requirement(self, auto_schema):
        assert self.name, 'name must be specified'
        return {self.name: []}

    @abstractmethod
    def get_security_definition(self, auto_schema):
        pass  # pragma: no cover


class OpenApiSerializerExtension(OpenApiGeneratorExtension['OpenApiSerializerExtension']):
    """

    """
    _registry: List['OpenApiSerializerExtension'] = []

    def get_name(self) -> Optional[str]:
        """ return str for overriding default name extraction """
        return None

    def map_serializer(self, auto_schema, direction):
        """ override for customized serializer mapping """
        return auto_schema._map_basic_serializer(self.target_class, direction)


class OpenApiSerializerFieldExtension(OpenApiGeneratorExtension['OpenApiSerializerFieldExtension']):
    """

    """
    _registry: List['OpenApiSerializerFieldExtension'] = []

    @abstractmethod
    def map_serializer_field(self, auto_schema, direction):
        pass  # pragma: no cover


class OpenApiViewExtension(OpenApiGeneratorExtension['OpenApiViewExtension']):
    """

    """
    _registry: List['OpenApiViewExtension'] = []

    @classmethod
    def _load_class(cls):
        super()._load_class()
        # special case @api_view: view class is nested in the cls attr of the function object
        if hasattr(cls.target_class, 'cls'):
            cls.target_class = cls.target_class.cls

    @abstractmethod
    def view_replacement(self):
        pass  # pragma: no cover


class OpenApiFilterExtension(OpenApiGeneratorExtension['OpenApiFilterExtension']):
    """

    """
    _registry: List['OpenApiFilterExtension'] = []

    @abstractmethod
    def get_schema_operation_parameters(self, auto_schema, *args, **kwargs):
        pass  # pragma: no cover
