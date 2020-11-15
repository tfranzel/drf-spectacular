import tempfile

import pytest
import yaml
from django.core import management
from django.urls import path
from rest_framework.decorators import api_view


def test_command_plain(capsys):
    management.call_command('spectacular', validate=True, fail_on_warn=True)
    schema_stdout = capsys.readouterr().out
    schema = yaml.load(schema_stdout, Loader=yaml.SafeLoader)
    assert 'openapi' in schema
    assert 'info' in schema
    assert 'paths' in schema


def test_command_parameterized(capsys):
    with tempfile.NamedTemporaryFile() as fh:
        management.call_command(
            'spectacular',
            '--validate',
            '--fail-on-warn',
            '--lang=de',
            '--generator-class=drf_spectacular.generators.SchemaGenerator',
            '--file=' + fh.name,
        )
        schema = yaml.load(fh.read(), Loader=yaml.SafeLoader)

    assert 'openapi' in schema
    assert 'info' in schema
    assert 'paths' in schema


@api_view(['GET'])
def func(request):
    pass  # pragma: no cover


urlpatterns = [path('func', func)]


def test_command_fail(capsys):
    with pytest.raises(RuntimeError):
        management.call_command(
            'spectacular',
            '--fail-on-warn',
            '--urlconf=tests.test_command',
        )
    stderr = capsys.readouterr().err
    assert 'Error #0: Unable to guess serializer' in stderr
    assert 'Schema generation summary:' in stderr
