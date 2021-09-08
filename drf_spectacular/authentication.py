from django.conf import settings

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.mixins import TokenSecuritySchemeMixin


class SessionScheme(OpenApiAuthenticationExtension):
    target_class = 'rest_framework.authentication.SessionAuthentication'
    name = 'cookieAuth'
    priority = -1

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'cookie',
            'name': settings.SESSION_COOKIE_NAME,
        }


class BasicScheme(OpenApiAuthenticationExtension):
    target_class = 'rest_framework.authentication.BasicAuthentication'
    name = 'basicAuth'
    priority = -1

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'basic',
        }


class TokenScheme(TokenSecuritySchemeMixin, OpenApiAuthenticationExtension):
    target_class = 'rest_framework.authentication.TokenAuthentication'
    name = 'tokenAuth'
    match_subclasses = True
    priority = -1

    def get_security_definition(self, auto_schema):
        header_name = 'Authorization'
        header_type = self.target.keyword
        return self.build_security_scheme(header_name, header_type)
