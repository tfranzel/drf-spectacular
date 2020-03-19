import yaml
from django.core import management


def test_command_plain(capsys):
    management.call_command('spectacular')

    schema_stdout = capsys.readouterr().out

    schema = yaml.load(schema_stdout, Loader=yaml.Loader)
    assert 'openapi' in schema
    assert 'servers' in schema
    assert 'paths' in schema
