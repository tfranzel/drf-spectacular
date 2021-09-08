from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.mixins import TokenSecuritySchemeMixin


class JWTScheme(TokenSecuritySchemeMixin, OpenApiAuthenticationExtension):
    target_class = 'rest_framework_jwt.authentication.JSONWebTokenAuthentication'
    name = 'jwtAuth'

    def get_security_definition(self, auto_schema):
        from rest_framework_jwt.settings import api_settings

        header_name = 'Authorization'
        header_type = api_settings.JWT_AUTH_HEADER_PREFIX
        extra = {'bearerFormat': 'JWT'}
        return self.build_security_scheme(header_name, header_type, **extra)
