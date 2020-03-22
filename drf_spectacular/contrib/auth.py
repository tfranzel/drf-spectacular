from django.views import View

from drf_spectacular.auth import OpenApiAuthenticationScheme


class SimpleJWTScheme(OpenApiAuthenticationScheme):
    authentication_class = 'rest_framework_simplejwt.authentication.JWTAuthentication'
    name = 'jwtAuth'

    @classmethod
    def get_security_definition(cls, view: View, authenticator):
        from rest_framework_simplejwt.settings import api_settings
        from drf_spectacular.plumbing import warn

        if len(api_settings.AUTH_HEADER_TYPES) > 1:
            warn(
                f'OpenAPI3 can only have one "bearerFormat". JWT Settings specify '
                f'{api_settings.AUTH_HEADER_TYPES}. Using the first one.'
            )
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': api_settings.AUTH_HEADER_TYPES[0],
        }


class DjangoOAuthToolkitScheme(OpenApiAuthenticationScheme):
    authentication_class = 'oauth2_provider.contrib.rest_framework.OAuth2Authentication'
    name = 'oauth2'

    @classmethod
    def get_security_requirement(cls, view: View, authenticator):
        # todo build proper scopes
        return {cls.name: view.required_scopes}

    @classmethod
    def get_security_definition(cls, view: View, authenticator):
        from drf_spectacular.app_settings import spectacular_settings
        from oauth2_provider.settings import oauth2_settings

        flows = {}
        for flow_type in spectacular_settings.OAUTH2_FLOWS:
            flows[flow_type] = {}
            if flow_type in ('implicit', 'authorizationCode'):
                flows[flow_type]['authorizationUrl'] = spectacular_settings.OAUTH2_AUTHORIZATION_URL
            if flow_type in ('password', 'clientCredentials', 'authorizationCode'):
                flows[flow_type]['tokenUrl'] = spectacular_settings.OAUTH2_TOKEN_URL
            if spectacular_settings.OAUTH2_REFRESH_URL:
                flows[flow_type]['refreshUrl'] = spectacular_settings.OAUTH2_REFRESH_URL
            if oauth2_settings.SCOPES:
                flows[flow_type]['scopes'] = oauth2_settings.SCOPES

        return {
            'type': 'oauth2',
            'flows': flows
        }
