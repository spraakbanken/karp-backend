import pytest

from typer import Typer
from typer.testing import CliRunner

from karp.main import config


@pytest.fixture(scope='session', name='runner')
def fixture_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(scope='session', name='cliapp')
def fixture_cliapp() -> Typer:
    from karp.cliapp.main import create_app
    return create_app()


class TestCli:
    def test_version(self, runner: CliRunner, cliapp: Typer):
        result = runner.invoke(cliapp, ['--version'])
        assert result.exit_code == 0
        assert f'{config.PROJECT_NAME} CLI {config.VERSION}\n' == result.stdout
