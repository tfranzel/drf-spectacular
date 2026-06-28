import io
import tempfile
from unittest import mock

import pytest
import yaml
from django.core import management
from django.core.management import CommandError, load_command_class
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


def test_command_help_text():
    """Regression test for #1175: every spectacular-specific flag must carry a
    `help=` description so that `./manage.py spectacular --help` is
    self-documenting and does not need to send users back to the source.
    """
    cmd = load_command_class('drf_spectacular', 'spectacular')
    parser = cmd.create_parser('manage.py', 'spectacular')
    # collect actions defined by the spectacular command (skip stock Django actions)
    spectacular_flags = {
        '--format', '--urlconf', '--generator-class', '--file', '--fail-on-warn',
        '--validate', '--api-version', '--lang', '--color', '--custom-settings',
    }
    actions_by_flag = {
        opt_str: action
        for action in parser._actions
        for opt_str in action.option_strings
        if opt_str in spectacular_flags
    }
    # all spectacular flags should be present and carry help text
    assert spectacular_flags <= set(actions_by_flag), (
        f"missing flags: {spectacular_flags - set(actions_by_flag)}"
    )
    missing_help = [
        flag for flag, action in actions_by_flag.items() if not (action.help or '').strip()
    ]
    assert not missing_help, (
        f"spectacular flags without help text: {missing_help}"
    )
    # also verify it surfaces in --help output
    buf = io.StringIO()
    parser.print_help(buf)
    help_text = buf.getvalue()
    for flag in spectacular_flags:
        # the help text follows the flag on the same or next line, so just
        # ensure the flag still appears at least once
        assert flag in help_text
