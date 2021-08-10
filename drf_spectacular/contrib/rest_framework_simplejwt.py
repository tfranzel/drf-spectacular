from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from drf_spectacular.drainage import warn
from drf_spectacular.extensions import OpenApiAuthenticationExtension, OpenApiSerializerExtension
from drf_spectacular.utils import inline_serializer


class TokenObtainPairSerializerExtension(OpenApiSerializerExtension):
    target_class = 'rest_framework_simplejwt.serializers.TokenObtainPairSerializer'

    def map_serializer(self, auto_schema, direction):
        Fixed = inline_serializer('Fixed', fields={
            self.target_class.username_field: serializers.CharField(write_only=True),
            'password': serializers.CharField(write_only=True),
            'access': serializers.CharField(read_only=True),
            'refresh': serializers.CharField(read_only=True),
        })
        return auto_schema._map_serializer(Fixed, direction)


class TokenObtainSlidingSerializerExtension(OpenApiSerializerExtension):
    target_class = 'rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer'

    def map_serializer(self, auto_schema, direction):
        Fixed = inline_serializer('Fixed', fields={
            self.target_class.username_field: serializers.CharField(write_only=True),
            'password': serializers.CharField(write_only=True),
            'token': serializers.CharField(read_only=True),
        })
        return auto_schema._map_serializer(Fixed, direction)


class TokenRefreshSerializerExtension(OpenApiSerializerExtension):
    target_class = 'rest_framework_simplejwt.serializers.TokenRefreshSerializer'

    def map_serializer(self, auto_schema, direction):
        from rest_framework_simplejwt.settings import api_settings

        if api_settings.ROTATE_REFRESH_TOKENS:
            class Fixed(serializers.Serializer):
                access = serializers.CharField(read_only=True)
                refresh = serializers.CharField()
        else:
            class Fixed(serializers.Serializer):
                access = serializers.CharField(read_only=True)
                refresh = serializers.CharField(write_only=True)

        return auto_schema._map_serializer(Fixed, direction)


class SimpleJWTScheme(OpenApiAuthenticationExtension):
    target_class = 'rest_framework_simplejwt.authentication.JWTAuthentication'
    name = 'jwtAuth'

    def get_security_definition(self, auto_schema):
        from rest_framework_simplejwt.settings import api_settings

        if len(api_settings.AUTH_HEADER_TYPES) > 1:
            warn(
                f'OpenAPI3 can only have one "bearerFormat". JWT Settings specify '
                f'{api_settings.AUTH_HEADER_TYPES}. Using the first one.'
            )
        header_name = getattr(api_settings, 'AUTH_HEADER_NAME', 'HTTP_AUTHORIZATION')

        if (
            api_settings.AUTH_HEADER_TYPES[0] == 'Bearer'
            and header_name == 'HTTP_AUTHORIZATION'
        ):
            return {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': "JWT",
            }
        else:
            if header_name.startswith('HTTP_'):
                header_name = header_name[5:]
            header_name = header_name.replace('_', '-').capitalize()
            return {
                'type': 'apiKey',
                'in': 'header',
                'name': header_name,
                'description': _(
                    'Token-based authentication with required prefix "%s"'
                ) % api_settings.AUTH_HEADER_TYPES[0]
            }


class SimpleJWTTokenUserScheme(SimpleJWTScheme):
    target_class = 'rest_framework_simplejwt.authentication.JWTTokenUserAuthentication'
