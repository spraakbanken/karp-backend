import pytest

from typer import Typer
from typer.testing import CliRunner


@pytest.fixture(scope='session', name='runner')
def fixture_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(scope='session', name='cliapp')
def fixture_cliapp() -> Typer:
    from karp.cliapp.main import create_app
    return create_app()


class TestCliResource:
    def test_help(self, runner: CliRunner, cliapp: Typer):
        result = runner.invoke(cliapp, ['resource', '--help'])
        result = runner.invoke(cliapp, ['resource', '--help'])
        assert result.exit_code == 0
