from typer.testing import CliRunner
from karp.lex.application import ResourceQueries

from karp.main import AppContext
from karp.cliapp.main import create_app

runner = CliRunner()
cliapp = create_app()


class TestCliResourceLifetime:
    def test_help(self):
        result = runner.invoke(cliapp, ["resource", "--help"])
        assert result.exit_code == 0

    def test_create_and_publish_repo(
        self,
        app_context: AppContext,
    ):
        result = runner.invoke(
            cliapp,
            [
                "resource",
                "create",
                "assets/testing/config/lexlex.json",
            ],
        )

        if isinstance(result.exception, Exception):
            raise result.exception
        else:
            assert result.exit_code == 0

        resource_queries = app_context.injector.get(ResourceQueries)
        assert resource_queries.by_resource_id_optional("lexlex") is not None
