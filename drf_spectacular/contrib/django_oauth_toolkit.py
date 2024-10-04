from drf_spectacular.extensions import OpenApiAuthenticationExtension


class DjangoOAuthToolkitScheme(OpenApiAuthenticationExtension):
    target_class = 'oauth2_provider.contrib.rest_framework.OAuth2Authentication'
    name: str = 'oauth2'

    def get_security_requirement(self, auto_schema):
        from oauth2_provider.contrib.rest_framework import (
            IsAuthenticatedOrTokenHasScope, TokenHasScope, TokenMatchesOASRequirements,
        )
        from rest_framework.permissions import AND, OR
        view = auto_schema.view
        request = view.request

        def security_requirement_from_permission(perm) -> list | dict | None:
            if isinstance(perm, (OR, AND)):
                return (
                    security_requirement_from_permission(perm.op1) or security_requirement_from_permission(perm.op2)
                )
            if isinstance(perm, TokenMatchesOASRequirements):
                alt_scopes = perm.get_required_alternate_scopes(request, view)
                alt_scopes = alt_scopes.get(auto_schema.method, [])
                return [{self.name: group} for group in alt_scopes]
            if isinstance(perm, IsAuthenticatedOrTokenHasScope):
                return {self.name: TokenHasScope().get_scopes(request, view)}
            if isinstance(perm, TokenHasScope):
                # catch-all for subclasses of TokenHasScope like TokenHasReadWriteScope
                return {self.name: perm.get_scopes(request, view)}
            return None

        security_requirements = map(security_requirement_from_permission, auto_schema.view.get_permissions())
        for requirement in security_requirements:
            if requirement is not None:
                return requirement

    def get_security_definition(self, auto_schema):
        from oauth2_provider.scopes import get_scopes_backend

        from drf_spectacular.settings import spectacular_settings

        flows = {}
        for flow_type in spectacular_settings.OAUTH2_FLOWS:
            flows[flow_type] = {}
            if flow_type in ('implicit', 'authorizationCode'):
                flows[flow_type]['authorizationUrl'] = spectacular_settings.OAUTH2_AUTHORIZATION_URL
            if flow_type in ('password', 'clientCredentials', 'authorizationCode'):
                flows[flow_type]['tokenUrl'] = spectacular_settings.OAUTH2_TOKEN_URL
            if spectacular_settings.OAUTH2_REFRESH_URL:
                flows[flow_type]['refreshUrl'] = spectacular_settings.OAUTH2_REFRESH_URL
            scope_backend = get_scopes_backend()
            flows[flow_type]['scopes'] = scope_backend.get_all_scopes()

        return {
            'type': 'oauth2',
            'flows': flows
        }
