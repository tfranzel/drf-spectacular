from abc import abstractmethod
from typing import List

from django.views import View

from drf_spectacular.plumbing import OpenApiGeneratorExtension


class OpenApiAuthenticationExtension(OpenApiGeneratorExtension['OpenApiAuthenticationExtension']):
    _registry: List['OpenApiAuthenticationExtension'] = []

    name: str

    def get_security_requirement(self, view: View):
        assert self.name, 'name must be specified'
        return {self.name: []}

    @abstractmethod
    def get_security_definition(self, view: View):
        pass


class SessionScheme(OpenApiAuthenticationExtension):
    target_class = 'rest_framework.authentication.SessionAuthentication'
    name = 'cookieAuth'

    def get_security_definition(self, view: View):
        return {
            'type': 'apiKey',
            'in': 'cookie',
            'name': 'Session',
        }


class BasicScheme(OpenApiAuthenticationExtension):
    target_class = 'rest_framework.authentication.BasicAuthentication'
    name = 'basicAuth'

    def get_security_definition(self, view: View):
        return {
            'type': 'http',
            'scheme': 'basic',
        }


class TokenScheme(OpenApiAuthenticationExtension):
    target_class = 'rest_framework.authentication.TokenAuthentication'
    name = 'tokenAuth'
    matches_subclass = True

    def get_security_definition(self, view: View):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': self.target.keyword,
        }
