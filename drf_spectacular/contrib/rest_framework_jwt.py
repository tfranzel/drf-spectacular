from drf_spectacular.extensions import OpenApiAuthenticationExtension


class JWTScheme(OpenApiAuthenticationExtension):
    target_class = 'rest_framework_jwt.authentication.JSONWebTokenAuthentication'
    name = 'jwtAuth'

    def get_security_definition(self, auto_schema):
        from rest_framework_jwt.settings import api_settings

        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': api_settings.JWT_AUTH_HEADER_PREFIX,
        }
