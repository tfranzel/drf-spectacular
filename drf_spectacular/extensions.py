from abc import abstractmethod
from typing import TYPE_CHECKING, List, Optional

from rest_framework.views import APIView

from drf_spectacular.plumbing import OpenApiGeneratorExtension

if TYPE_CHECKING:
    from drf_spectacular.openapi import AutoSchema


class OpenApiAuthenticationExtension(OpenApiGeneratorExtension['OpenApiAuthenticationExtension']):
    """

    """
    _registry: List['OpenApiAuthenticationExtension'] = []

    name: str

    def get_security_requirement(self, auto_schema: 'AutoSchema'):
        assert self.name, 'name must be specified'
        return {self.name: []}

    @abstractmethod
    def get_security_definition(self, auto_schema: 'AutoSchema'):
        pass  # pragma: no cover


class OpenApiSerializerExtension(OpenApiGeneratorExtension['OpenApiSerializerExtension']):
    """

    """
    _registry: List['OpenApiSerializerExtension'] = []

    def get_name(self) -> Optional[str]:
        """ return str for overriding default name extraction """
        return None

    def map_serializer(self, auto_schema: 'AutoSchema', direction):
        """ override for customized serializer mapping """
        return auto_schema._map_basic_serializer(self.target_class, direction)


class OpenApiSerializerFieldExtension(OpenApiGeneratorExtension['OpenApiSerializerFieldExtension']):
    """

    """
    _registry: List['OpenApiSerializerFieldExtension'] = []

    def get_name(self) -> Optional[str]:
        """ return str for breaking out field schema into separate component """
        return None

    @abstractmethod
    def map_serializer_field(self, auto_schema: 'AutoSchema', direction):
        """ override for customized serializer field mapping """
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
    def view_replacement(self) -> APIView:
        pass  # pragma: no cover


class OpenApiFilterExtension(OpenApiGeneratorExtension['OpenApiFilterExtension']):
    """

    """
    _registry: List['OpenApiFilterExtension'] = []

    @abstractmethod
    def get_schema_operation_parameters(self, auto_schema: 'AutoSchema', *args, **kwargs) -> List[dict]:
        pass  # pragma: no cover
