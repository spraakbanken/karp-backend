import pytest

from typer import Typer
from typer.testing import CliRunner

from karp.main import config


class TestCli:
    def test_version(self, runner: CliRunner, cliapp: Typer):
        result = runner.invoke(cliapp, ["--version"])
        assert result.exit_code == 0
        assert f"{config.PROJECT_NAME} CLI {config.VERSION}\n" == result.stdout
