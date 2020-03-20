import yaml
from django.core import management


def test_command_plain(capsys):
    management.call_command('spectacular', validate=True, fail_on_warn=True)

    schema_stdout = capsys.readouterr().out
    schema = yaml.load(schema_stdout, Loader=yaml.SafeLoader)
    assert 'openapi' in schema
    assert 'info' in schema
    assert 'paths' in schema
