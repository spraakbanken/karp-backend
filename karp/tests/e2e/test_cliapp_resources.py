import pytest

from typer import Typer
from typer.testing import CliRunner
from karp import lex

from karp.main import AppContext


class TestCliResourceLifetime:
    def test_help(self, runner: CliRunner, cliapp: Typer):
        result = runner.invoke(cliapp, ["resource", "--help"])
        assert result.exit_code == 0

    def test_create_and_publish_repo(
        self,
        runner: CliRunner,
        cliapp: Typer,
        app_context: AppContext,
    ):
        result = runner.invoke(
            cliapp, ["entry-repo", "create", "karp/tests/data/config/lexlex.json"]
        )
        print(f"{result.stdout=}")
        assert result.exit_code == 0

        entry_repo_repo = app_context.container.get(lex.ReadOnlyEntryRepoRepositry)  # type: ignore [misc]
        entry_repo = entry_repo_repo.get_by_name("lexlex")
        assert entry_repo is not None

        result = runner.invoke(
            cliapp,
            [
                "resource",
                "create",
                "karp/tests/data/config/lexlex.json",
                "--entry-repo-id",
                str(entry_repo.entity_id),
            ],
        )
        print(f"{result.stdout=}")
        assert result.exit_code == 0

        resource_repo = app_context.container.get(lex.ReadOnlyResourceRepository)  # type: ignore [misc]
        assert resource_repo.get_by_resource_id("lexlex") is not None

    @pytest.mark.xfail(reason="not ready")
    def test_update_entry_repo(
        self,
        runner: CliRunner,
        cliapp: Typer,
        app_context: AppContext,
    ):
        result = runner.invoke(
            cliapp, ["entry-repo", "create", "karp/tests/data/config/lexlex.json"]
        )
        print(f"{result.stdout=}")
        assert result.exit_code == 0

        entry_repo_repo = app_context.container.get(lex.ReadOnlyEntryRepoRepositry)  # type: ignore [misc]
        entry_repo = entry_repo_repo.get_by_name("lexlex")
        assert entry_repo is not None

        result = runner.invoke(
            cliapp,
            [
                "resource",
                "set-entry-repo",
                "lexlex",
                str(entry_repo.entity_id),
            ],
        )
        print(f"{result.stdout=}")
        assert result.exit_code == 0

        resource_repo = app_context.container.get(lex.ReadOnlyResourceRepository)  # type: ignore [misc]
        resource_lexlex = resource_repo.get_by_resource_id("lexlex")
        assert resource_lexlex.entry_repository_id == entry_repo.entity_id
