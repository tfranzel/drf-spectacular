from django.utils.translation import gettext_lazy as _

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class SessionScheme(OpenApiAuthenticationExtension):
    target_class = 'rest_framework.authentication.SessionAuthentication'
    name = 'cookieAuth'
    priority = -1

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'cookie',
            'name': 'Session',
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


class TokenScheme(OpenApiAuthenticationExtension):
    target_class = 'rest_framework.authentication.TokenAuthentication'
    name = 'tokenAuth'
    match_subclasses = True
    priority = -1

    def get_security_definition(self, auto_schema):
        if self.target.keyword == 'Bearer':
            return {
                'type': 'http',
                'scheme': 'bearer',
            }
        else:
            return {
                'type': 'apiKey',
                'in': 'header',
                'name': 'Authorization',
                'description': _(
                    'Token-based authentication with required prefix "%s"'
                ) % self.target.keyword
            }
