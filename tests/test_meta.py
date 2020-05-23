from unittest import mock

from rest_framework.views import APIView

from tests import generate_schema

META = {
    'TITLE': 'Spectacular API',
    'DESCRIPTION': 'auto-generated spectacular schema for your API',
    'TOS': 'https://github.com/tfranzel/drf-spectacular/blob/master/LICENSE',
    'CONTACT': {
        "name": "API Support",
        "url": "https://github.com/tfranzel/drf-spectacular/issues",
        "email": "support@example.com"
    },
    'LICENSE': {
        'name': 'BSD 3-Clause',
        'url': 'https://github.com/tfranzel/drf-spectacular/blob/master/LICENSE',
    },
    'VERSION': '1.0.0',
    'SERVERS': [
        {
            "url": "https://gigantic-server.com/v1",
            "description": "Production server"
        },
        {
            "url": "https://development.gigantic-server.com/v1",
            "description": "Development server"
        }
    ],
    'TAGS': [{
        "name": "awesome-tag",
        "description": "Operations that are awesome"
    }],
    'EXTERNAL_DOCS': {
        "url": "https://gigantic-server.com/documentation",
        "description": "Documentation for API usage"
    },
}


def build_settings_mock(name):
    return (f'drf_spectacular.settings.spectacular_settings.{name}', META[name])


@mock.patch(*build_settings_mock('TITLE'))
@mock.patch(*build_settings_mock('DESCRIPTION'))
@mock.patch(*build_settings_mock('TOS'))
@mock.patch(*build_settings_mock('CONTACT'))
@mock.patch(*build_settings_mock('LICENSE'))
@mock.patch(*build_settings_mock('VERSION'))
@mock.patch(*build_settings_mock('SERVERS'))
@mock.patch(*build_settings_mock('TAGS'))
@mock.patch(*build_settings_mock('EXTERNAL_DOCS'))
def test_append_extra_components(no_warnings):
    class XAPIView(APIView):
        pass

    schema = generate_schema('x', view=XAPIView)
    assert schema['info']['version'] == '1.0.0'
    assert schema['info']['description']
    assert 'termsOfService' in schema['info']
    assert 'servers' in schema
    assert 'externalDocs' in schema
