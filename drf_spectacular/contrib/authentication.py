from django.views import View

from drf_spectacular.authentication import OpenApiAuthenticationExtension


class SimpleJWTScheme(OpenApiAuthenticationExtension):
    target_class = 'rest_framework_simplejwt.authentication.JWTAuthentication'
    name = 'jwtAuth'

    def get_security_definition(self, view: View):
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


class DjangoOAuthToolkitScheme(OpenApiAuthenticationExtension):
    target_class = 'oauth2_provider.contrib.rest_framework.OAuth2Authentication'
    name = 'oauth2'

    def get_security_requirement(self, view: View):
        # todo build proper scopes
        return {self.name: view.required_scopes}

    def get_security_definition(self, view: View):
        from drf_spectacular.settings import spectacular_settings
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
