import pytest

from typer import Typer
from typer.testing import CliRunner
from karp.lex import ReadOnlyEntryRepoRepositry

from karp.main import AppContext


class TestCliResourceLifetime:
    def test_help(self, runner: CliRunner, cliapp: Typer):
        result = runner.invoke(cliapp, ['resource', '--help'])
        assert result.exit_code == 0

    def test_create_and_publish_repo(
        self,
        runner: CliRunner,
        cliapp: Typer,
        app_context: AppContext,
    ):
        result = runner.invoke(
            cliapp, ['entry-repo', 'create', 'karp/tests/data/config/lexlex.json'])
        print(f'{result.stdout=}')
        assert result.exit_code == 0

        entry_repo_repo = app_context.container.get(ReadOnlyEntryRepoRepositry)

        assert entry_repo_repo.get_by_name('lexlex') is not None
