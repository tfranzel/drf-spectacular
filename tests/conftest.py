import os
import re
from importlib import import_module

import django
import pytest
from django import __version__ as DJANGO_VERSION
from django.core import management

from tests import is_gis_installed


def pytest_configure(config):
    from django.conf import settings

    config.addinivalue_line(
        "markers", "contrib(name): mark required contrib package"
    )

    contrib_apps = [
        'dj_rest_auth',
        'dj_rest_auth.registration',
        'allauth',
        'allauth.account',
        'allauth.socialaccount',
        'oauth2_provider',
        'django_filters',
        'knox',
        # this is not strictly required and when added django-polymorphic
        # currently breaks the whole Django/DRF upstream testing.
        # 'polymorphic',
        # 'rest_framework_jwt',
    ]
    try:
        from allauth import __version__ as allauth_version
    except ImportError:
        allauth_version = ""

    # only load GIS if library is installed. This is required for the GIS test to work
    if is_gis_installed():
        contrib_apps.append('rest_framework_gis')

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    settings.configure(
        DEBUG_PROPAGATE_EXCEPTIONS=True,
        DATABASES={'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:'
        }},
        SITE_ID=1,
        SECRET_KEY='not very secret in tests',
        USE_I18N=True,
        USE_L10N=True,
        LANGUAGES=[
            ('de-de', 'German'),
            ('en-us', 'English'),
        ],
        LOCALE_PATHS=[
            base_dir + '/locale/'
        ],
        STATIC_URL='/static/',
        ROOT_URLCONF='tests.urls',
        TEMPLATES=[
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [],
                'APP_DIRS': True,
                'OPTIONS': {
                    'context_processors': [
                        'django.template.context_processors.debug',
                    ],
                },
            },
        ],
        MIDDLEWARE=(
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            *(['allauth.account.middleware.AccountMiddleware'] if allauth_version > "0.60.0" else []),
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.middleware.locale.LocaleMiddleware',
        ),
        INSTALLED_APPS=(
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'rest_framework',
            'rest_framework.authtoken',
            *[app for app in contrib_apps if module_available(app)],
            'drf_spectacular',
            'tests',
        ),
        PASSWORD_HASHERS=(
            'django.contrib.auth.hashers.SHA1PasswordHasher',
            'django.contrib.auth.hashers.PBKDF2PasswordHasher',
            'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
            'django.contrib.auth.hashers.BCryptPasswordHasher',
            'django.contrib.auth.hashers.MD5PasswordHasher',
            'django.contrib.auth.hashers.CryptPasswordHasher',
        ),
        REST_FRAMEWORK={
            'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
            'PAGE_SIZE': 10,
        },
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
        SILENCED_SYSTEM_CHECKS=[
            'rest_framework.W001', 'fields.E210', 'security.W001', 'security.W002',
            'security.W003', 'security.W009', 'security.W012'
        ],
    )

    django.setup()
    # For whatever reason this works locally without an issue.
    # on TravisCI content_type table is missing in the sqlite db as
    # if no migration ran, but then why does it work locally?!
    management.call_command('migrate')


def pytest_addoption(parser):
    parser.addoption(
        "--skip-missing-contrib",
        action="store_true",
        default=False,
        help="skip tests depending on missing contrib packages"
    )
    parser.addoption(
        "--allow-contrib-fail",
        action="store_true",
        default=False,
        help="run contrib tests but allow them to fail"
    )
    parser.addoption(
        "--allow-skip-extra-system-req",
        action="store_true",
        default=False,
        help=""
    )


def pytest_collection_modifyitems(config, items):
    skip_missing_contrib = pytest.mark.skip(reason="skip tests for missing contrib package")
    allow_contrib_fail = pytest.mark.xfail(reason="contrib test were allowed to fail")
    allow_sys_requirement_fail = pytest.mark.xfail(reason="may fail due to missing system library")

    for item in items:
        for marker in item.own_markers:
            if marker.name == 'contrib' and config.getoption("--skip-missing-contrib"):
                if not all([module_available(module_str) for module_str in marker.args]):  # pragma: no cover
                    item.add_marker(skip_missing_contrib)
            if marker.name == 'contrib' and config.getoption("--allow-contrib-fail"):
                item.add_marker(allow_contrib_fail)
            if marker.name == 'system_requirement_fulfilled' and config.getoption("--allow-skip-extra-system-req"):
                if not marker.args[0]:
                    item.add_marker(allow_sys_requirement_fail)


@pytest.fixture()
def no_warnings(capsys):
    """ make sure test emits no warnings """
    yield capsys
    captured = capsys.readouterr()
    assert not captured.out
    assert not captured.err


@pytest.fixture()
def warnings(capsys):
    """ make sure test emits no warnings """
    yield capsys
    captured = capsys.readouterr()
    assert captured.err


@pytest.fixture()
def clear_generator_settings():
    from drf_spectacular.drainage import GENERATOR_STATS
    yield
    GENERATOR_STATS._trace_lineno = False
    GENERATOR_STATS._red = GENERATOR_STATS._blue = ''
    GENERATOR_STATS._yellow = GENERATOR_STATS._clear = ''


@pytest.fixture()
def clear_caches():
    from drf_spectacular.plumbing import _load_enum_name_overrides, get_openapi_type_mapping
    _load_enum_name_overrides.cache_clear()
    get_openapi_type_mapping.cache_clear()
    yield
    _load_enum_name_overrides.cache_clear()
    get_openapi_type_mapping.cache_clear()


def module_available(module_str):
    try:
        import_module(module_str)
    except ImportError:
        return False
    else:
        return True


@pytest.fixture()
def django_transforms():
    def integer_field_sqlite(s):
        return re.sub(
            r' *maximum: 9223372036854775807\n *minimum: (-9223372036854775808|0)\n *format: int64\n',
            '',
            s,
            flags=re.M
        )

    if DJANGO_VERSION >= '5':
        return [integer_field_sqlite]
    else:
        return []
