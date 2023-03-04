import tempfile
from unittest import mock

import pytest
import yaml
from django.core import management
from django.core.management import CommandError
from django.core.management.base import SystemCheckError
from django.urls import path
from rest_framework.decorators import api_view


def test_command_plain(capsys, clear_generator_settings):
    management.call_command('spectacular', validate=True, fail_on_warn=True)
    schema_stdout = capsys.readouterr().out
    schema = yaml.load(schema_stdout, Loader=yaml.SafeLoader)
    assert 'openapi' in schema
    assert 'info' in schema
    assert 'paths' in schema


def test_command_parameterized(clear_generator_settings):
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


def test_command_fail(capsys, clear_generator_settings):
    with pytest.raises(CommandError):
        management.call_command(
            'spectacular',
            '--fail-on-warn',
            '--urlconf=tests.test_command',
        )
    stderr = capsys.readouterr().err
    assert '/tests/test_command.py: Error [func]: unable to guess serializer' in stderr
    assert 'Schema generation summary:' in stderr


def test_command_color(capsys, clear_generator_settings):
    management.call_command(
        'spectacular',
        '--color',
        '--urlconf=tests.test_command',
    )
    stderr = capsys.readouterr().err
    assert '\033[0;31mError [func]:' in stderr


CUSTOM = {'DESCRIPTION': 'custom setting'}


def test_command_custom_settings(capsys, clear_generator_settings):
    management.call_command('spectacular', '--custom-settings=tests.test_command.CUSTOM')
    assert 'description: custom setting' in capsys.readouterr().out


def test_command_check(capsys):
    management.call_command('check', '--deploy')
    stderr = capsys.readouterr().err
    assert not stderr


@api_view(['GET'])
def func(request):
    pass  # pragma: no cover


urlpatterns = [path('func', func)]


@mock.patch('tests.urls.urlpatterns', [path('api/endpoint/', func)])
def test_command_check_fail(capsys):
    with pytest.raises(SystemCheckError):
        management.call_command('check', '--fail-level', 'WARNING', '--deploy')
    management.call_command('check', '--deploy')
    stdout = capsys.readouterr().err
    assert 'System check identified some issues' in stdout
    assert 'drf_spectacular.W002' in stdout
