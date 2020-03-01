from rest_framework_simplejwt.authentication import JWTAuthentication

from drf_spectacular.auth import OpenApiAuthenticationScheme


class JWTAuthenticationScheme(OpenApiAuthenticationScheme):
    authentication_class = JWTAuthentication
    name = 'jwtAuth'
    schema = {
        'type': 'http',
        'scheme': 'bearer',
        'bearerFormat': 'Bearer',
    }
