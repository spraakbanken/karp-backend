import pytest  # noqa: I001

from typer import Typer
from typer.testing import CliRunner
from karp import lex
from karp.lex_infrastructure import SqlReadOnlyResourceRepository

from karp.main import AppContext


class TestCliResourceLifetime:
    def test_help(self, runner: CliRunner, cliapp: Typer):  # noqa: ANN201
        result = runner.invoke(cliapp, ["resource", "--help"])
        assert result.exit_code == 0

    def test_create_and_publish_repo(  # noqa: ANN201
        self,
        runner: CliRunner,
        cliapp: Typer,
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
        # print(f"{result.stdout=}")
        if isinstance(result.exception, Exception):
            raise result.exception
        else:
            assert result.exit_code == 0

        resource_repo = app_context.container.get(SqlReadOnlyResourceRepository)  # type: ignore [misc]
        assert resource_repo.by_resource_id_optional("lexlex") is not None
