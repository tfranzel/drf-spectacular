from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object

class AdfsAccessTokenAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = 'django_auth_adfs.rest_framework.AdfsAccessTokenAuthentication'
    name = 'jwtAuth'

    def get_security_definition(self, auto_schema):
        return build_bearer_security_scheme_object(header_name='AUTHORIZATION',
                                                   token_prefix='Bearer',
                                                   bearer_format='JWT')
