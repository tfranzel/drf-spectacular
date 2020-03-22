from abc import ABC, abstractmethod
from typing import List, Type, Optional, Any

from django.utils.module_loading import import_string
from django.views import View


class OpenApiAuthenticationScheme(ABC):
    _registry: List[Type['OpenApiAuthenticationScheme']] = []
    matches_subclass = False

    authentication_class: Any = None
    name: str

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._registry.append(cls)

    @classmethod
    def _matches(cls, authenticator) -> bool:
        if isinstance(cls.authentication_class, str):
            try:
                cls.authentication_class = import_string(cls.authentication_class)
            except ImportError:
                cls.authentication_class = None

        if cls.authentication_class is None:
            return False  # app not installed
        elif cls.matches_subclass:
            return issubclass(authenticator.__class__, cls.authentication_class)
        else:
            return authenticator.__class__ == cls.authentication_class

    @classmethod
    def get_match(cls, authenticator) -> Optional[Type['OpenApiAuthenticationScheme']]:
        for scheme in cls._registry:
            if scheme._matches(authenticator):
                return scheme
        return None

    @classmethod
    def get_security_requirement(cls, view: View, authenticator):
        assert cls.name, 'name must be specified'
        return {cls.name: []}

    @classmethod
    @abstractmethod
    def get_security_definition(cls, view: View, authenticator):
        pass


class SessionScheme(OpenApiAuthenticationScheme):
    authentication_class = 'rest_framework.authentication.SessionAuthentication'
    name = 'cookieAuth'

    @classmethod
    def get_security_definition(cls, view: View, authenticator):
        return {
            'type': 'apiKey',
            'in': 'cookie',
            'name': 'Session',
        }


class BasicScheme(OpenApiAuthenticationScheme):
    authentication_class = 'rest_framework.authentication.BasicAuthentication'
    name = 'basicAuth'

    @classmethod
    def get_security_definition(cls, view: View, authenticator):
        return {
            'type': 'http',
            'scheme': 'basic',
        }


class TokenScheme(OpenApiAuthenticationScheme):
    authentication_class = 'rest_framework.authentication.TokenAuthentication'
    name = 'tokenAuth'
    matches_subclass = True

    @classmethod
    def get_security_definition(cls, view: View, authenticator):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': authenticator.keyword,
        }
