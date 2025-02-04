from typer.testing import CliRunner

from karp.cliapp.main import create_app
from karp.main import config

runner = CliRunner()
cliapp = create_app()


class TestCli:
    def test_version(self):
        result = runner.invoke(cliapp, ["--version"])
        assert result.exit_code == 0
        assert f"{config.PROJECT_NAME} CLI {config.VERSION}\n" == result.stdout
