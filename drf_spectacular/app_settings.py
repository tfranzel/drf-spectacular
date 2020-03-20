from django.conf import settings
from rest_framework.settings import APISettings

SPECTACULAR_DEFAULTS = {
    'SCHEMA_AUTHENTICATION_CLASSES': [
        'drf_spectacular.auth.SessionAuthenticationScheme',
        'drf_spectacular.auth.BasicAuthenticationScheme',
        'drf_spectacular.auth.TokenAuthenticationScheme',
    ],
    'SCHEMA_PATH_PREFIX': r'',
    'OPERATION_SORTER': 'alpha',
    'DEFAULT_GENERATOR_CLASS': 'drf_spectacular.openapi.SchemaGenerator',
    'SERVE_URLCONF': None,
    'SERVE_PUBLIC': True,
    'SERVE_INCLUDE_SCHEMA': True,
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'APPEND_PATHS': {},
    'APPEND_COMPONENTS': {},
    # default schema metadata. refer to spec for valid inputs
    # https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.3.md#openapi-object
    'TITLE': '',
    'DESCRIPTION': '',
    'TOS': None,
    # Optional: MAY contain "name", "url", "email"
    'CONTACT': {},
    # Optional: MUST contain "name", MAY contain URL
    'LICENSE': {},
    'VERSION': '0.0.0',
    # Optional list of dicts: MUST contain "url", MAY contain "description", "variables"
    'SERVERS': [],
    'SECURITY': None,
    'TAGS': [],
    # Optional: MUST contain 'url', may contain "description"
    'EXTERNAL_DOCS': {},
}

IMPORT_STRINGS = [
    'SCHEMA_AUTHENTICATION_CLASSES',
    'DEFAULT_GENERATOR_CLASS',
    'SERVE_PERMISSIONS',
]

spectacular_settings = APISettings(
    user_settings=getattr(settings, 'SPECTACULAR_SETTINGS', {}),
    defaults=SPECTACULAR_DEFAULTS,
    import_strings=IMPORT_STRINGS,
)
