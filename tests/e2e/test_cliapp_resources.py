import pytest  # noqa: I001

from typer import Typer
from typer.testing import CliRunner
from karp import lex

from karp.main import AppContext

import sqlalchemy as sa
from sqlalchemy.engine import Connection, Engine
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base


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
            cliapp, ["entry-repo", "create", "assets/testing/config/places.json"]
        )

        engine = app_context.container.get(Engine)

        print(f"{result.stdout=}")
        assert result.exit_code == 0

        entry_repo_repo = app_context.container.get(lex.ReadOnlyEntryRepoRepository)  # type: ignore [misc]
        entry_repo = entry_repo_repo.get_by_name("places")
        assert entry_repo is not None
        print(entry_repo.entity_id)

        result = runner.invoke(
            cliapp,
            [
                "resource",
                "create",
                "assets/testing/config/places.json",
                "--entry-repo-id",
                str(entry_repo.entity_id),
            ],
        )

        print(f"{result.stdout=}")
        assert result.exit_code == 0

        result2 = runner.invoke(
            cliapp,
            [
                "entries",
                "add",
                "places",
                "assets/testing/data/places.jsonl",
            ],
        )
        print(f"{result2.stdout=}")
        assert result2.exit_code == 0

        result3 = runner.invoke(
            cliapp,
            [
                "resource",
                "publish",
                "places",
                "1",
            ],
        )
        print(f"{result3.stdout=}")
        assert result3.exit_code == 0

        resource_repo = app_context.container.get(lex.ReadOnlyResourceRepository)  # type: ignore [misc]
        assert resource_repo.get_by_resource_id("places") is not None

        entry_repo_uow = app_context.container.get(lex.EntryUowRepositoryUnitOfWork)
        r_repo = resource_repo.get_by_resource_id("places")

        with entry_repo_uow as uow:
            entry_repo = uow.repo.get_by_id(r_repo.entry_repository_id)
            assert sa.inspect(engine).has_table(entry_repo.table_name())

    def test_delete_resource(  # noqa: ANN201
        self,
        runner: CliRunner,
        cliapp: Typer,
        app_context: AppContext,
    ):
        result = runner.invoke(
            cliapp,
            ["resource", "delete", "places"],
        )
        print(f"{result.stdout=}")
        assert result.exit_code == 0

        engine = app_context.container.get(Engine)

        resource_repo = app_context.container.get(lex.ReadOnlyResourceRepository)
        entry_repo_repo = app_context.container.get(lex.ReadOnlyEntryRepoRepository)

        r_repo = resource_repo.get_by_resource_id("places")
        # Check that resource is marked as discarded in resource table
        assert r_repo is not None and r_repo.discarded
        e_repo = entry_repo_repo.get_by_name("places")
        assert e_repo is not None

        entry_repo_uow = app_context.container.get(lex.EntryUowRepositoryUnitOfWork)
        with entry_repo_uow as uow:
            entry_repo = uow.repo.get_by_id(r_repo.entry_repository_id)
            # Check that the data table was deleted
            assert not sa.inspect(engine).has_table(entry_repo.table_name())

        # check that elastic search indices have been deleted
