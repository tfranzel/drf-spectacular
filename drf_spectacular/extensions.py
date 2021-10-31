from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, Union

from drf_spectacular.plumbing import OpenApiGeneratorExtension
from drf_spectacular.utils import Direction

if TYPE_CHECKING:
    from rest_framework.views import APIView

    from drf_spectacular.openapi import AutoSchema


class OpenApiAuthenticationExtension(OpenApiGeneratorExtension['OpenApiAuthenticationExtension']):
    """
    Extension for specifying authentication schemes.

    The common use-case usually consists of setting a ``name`` string and returning a dict from
    ``get_security_definition``. To model a group of headers that go together, set a list
    of names and return a corresponding list of definitions from ``get_security_definition``.

    The view class is available via ``auto_schema.view``, while the original authentication class
    can be accessed via ``self.target``. If you want to override an included extension, be sure to
    set a higher matching priority by setting the class attribute ``priority = 1`` or higher.

    ``get_security_definition()`` is expected to return a valid `OpenAPI security scheme object
    <https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#security-scheme-object>`_
    """
    _registry: List['OpenApiAuthenticationExtension'] = []

    name: Union[str, List[str]]

    def get_security_requirement(self, auto_schema: 'AutoSchema') -> Dict[str, List[Any]]:
        assert self.name, 'name(s) must be specified'
        if isinstance(self.name, str):
            return {self.name: []}
        else:
            return {name: [] for name in self.name}

    @abstractmethod
    def get_security_definition(self, auto_schema: 'AutoSchema') -> Union[dict, List[dict]]:
        pass  # pragma: no cover


class OpenApiSerializerExtension(OpenApiGeneratorExtension['OpenApiSerializerExtension']):
    """
    Extension for replacing an insufficient or specifying an unknown Serializer schema.

    The existing implementation of ``map_serializer()`` will generate the same result
    as `drf-spectacular` would. Either augment or replace the generated schema. The
    view instance is available via ``auto_schema.view``, while the original serializer
    can be accessed via ``self.target``.

    ``map_serializer()`` is expected to return a valid `OpenAPI schema object
    <https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#schema-object>`_.
    """
    _registry: List['OpenApiSerializerExtension'] = []

    def get_name(self) -> Optional[str]:
        """ return str for overriding default name extraction """
        return None

    def map_serializer(self, auto_schema: 'AutoSchema', direction: Direction):
        """ override for customized serializer mapping """
        return auto_schema._map_serializer(self.target_class, direction, bypass_extensions=True)


class OpenApiSerializerFieldExtension(OpenApiGeneratorExtension['OpenApiSerializerFieldExtension']):
    """
    Extension for replacing an insufficient or specifying an unknown SerializerField schema.

    To augment the default schema, you can get what `drf-spectacular` would generate with
    ``auto_schema._map_serializer_field(self.target, direction, bypass_extensions=True)``.
    and edit the returned schema at your discretion. Beware that this may still emit
    warnings, in which case manual construction is advisable.

    ``map_serializer_field()`` is expected to return a valid `OpenAPI schema object
    <https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#schema-object>`_.
    """
    _registry: List['OpenApiSerializerFieldExtension'] = []

    def get_name(self) -> Optional[str]:
        """ return str for breaking out field schema into separate named component """
        return None

    @abstractmethod
    def map_serializer_field(self, auto_schema: 'AutoSchema', direction: Direction):
        """ override for customized serializer field mapping """
        pass  # pragma: no cover


class OpenApiViewExtension(OpenApiGeneratorExtension['OpenApiViewExtension']):
    """
    Extension for replacing discovered views with a more schema-appropriate/annotated version.

    ``view_replacement()`` is expected to return a subclass of ``APIView`` (which includes
    ``ViewSet`` et al.). The discovered original view instance can be accessed with
    ``self.target`` and be subclassed if desired.
    """
    _registry: List['OpenApiViewExtension'] = []

    @classmethod
    def _load_class(cls):
        super()._load_class()
        # special case @api_view: view class is nested in the cls attr of the function object
        if hasattr(cls.target_class, 'cls'):
            cls.target_class = cls.target_class.cls

    @abstractmethod
    def view_replacement(self) -> 'Type[APIView]':
        pass  # pragma: no cover


class OpenApiFilterExtension(OpenApiGeneratorExtension['OpenApiFilterExtension']):
    """
    Extension for specifying a list of filter parameters for a given ``FilterBackend``.

    The original filter class object can be accessed via ``self.target``. The attached view
    is accessible via ``auto_schema.view``.

    ``get_schema_operation_parameters()`` is expected to return either an empty list or a list
    of valid `OpenAPI parameter objects
    <https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#parameterObject>`_.
    """
    _registry: List['OpenApiFilterExtension'] = []

    @abstractmethod
    def get_schema_operation_parameters(self, auto_schema: 'AutoSchema', *args, **kwargs) -> List[dict]:
        pass  # pragma: no cover
