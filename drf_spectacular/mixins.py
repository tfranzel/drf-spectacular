from typing import Dict

from django.utils.translation import gettext_lazy as _


class TokenSecuritySchemeMixin:

    def build_security_scheme(self, header_name: str, header_type: str, **extra: str) -> Dict[str, str]:
        if header_name == 'Authorization' and header_type == 'Bearer':
            return {
                'type': 'http',
                'scheme': 'bearer',
                **extra,
            }
        else:
            return {
                'type': 'apiKey',
                'in': 'header',
                'name': header_name,
                'description': _('Token-based authentication with required prefix "%s"') % header_type,
            }
