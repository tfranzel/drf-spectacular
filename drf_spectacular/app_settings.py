from django.conf import settings
from rest_framework.settings import APISettings

SPECTACULAR_DEFAULTS = {
    'SCHEMA_AUTHENTICATION_CLASSES': [
        'drf_spectacular.auth.SessionAuthenticationScheme',
        'drf_spectacular.auth.BasicAuthenticationScheme',
        'drf_spectacular.auth.TokenAuthenticationScheme',
    ],
    'SCHEMA_PATH_PREFIX': r'',
}

IMPORT_STRINGS = [
    'SCHEMA_AUTHENTICATION_CLASSES',
]

spectacular_settings = APISettings(
    user_settings=getattr(settings, 'SPECTACULAR_SETTINGS', {}),
    defaults=SPECTACULAR_DEFAULTS,
    import_strings=IMPORT_STRINGS,
)
