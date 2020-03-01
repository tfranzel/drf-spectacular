from rest_framework import authentication


class OpenApiAuthenticationScheme:
    authentication_class = None
    name = None
    schema = None


class SessionAuthenticationScheme(OpenApiAuthenticationScheme):
    authentication_class = authentication.SessionAuthentication
    name = 'cookieAuth'
    schema = {
        'type': 'apiKey',
        'in': 'cookie',
        'name': 'Session',
    }


class BasicAuthenticationScheme(OpenApiAuthenticationScheme):
    authentication_class = authentication.BasicAuthentication
    name = 'basicAuth'
    schema = {
        'type': 'http',
        'scheme': 'basic',
    }


class TokenAuthenticationScheme(OpenApiAuthenticationScheme):
    authentication_class = authentication.TokenAuthentication
    name = 'tokenAuth'
    schema = {
        'type': 'http',
        'scheme': 'bearer',
        'bearerFormat': 'Token',
    }
