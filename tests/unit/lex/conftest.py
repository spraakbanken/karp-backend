import injector  # noqa: I001
import pytest

from karp.command_bus import CommandBus
from karp.lex import Lex
from karp.lex_core import commands as lex_commands  # noqa: F401
from karp.lex.application.repositories import (
    EntryUowRepositoryUnitOfWork,  # noqa: F401
)
from karp.main.modules import CommandBusMod, EventBusMod

from .adapters import (
    InMemoryEntryUowRepositoryUnitOfWork,  # noqa: F401
    # InMemoryEntryUowFactory,
    InMemoryResourceUnitOfWork,  # noqa: F401
)
from . import adapters, factories  # noqa: F401


# @pytest.fixture(name="entry_repo_repo_uow")
# def fixture_entry_repo_repo_uow() -> EntryUowRepositoryUnitOfWork:
#     return InMemoryEntryUowRepositoryUnitOfWork()


# @pytest.fixture(name="create_entry_repository")
# def fixture_create_entry_repository() -> lex_commands.CreateEntryRepository:
#     return factories.CreateEntryRepositoryFactory()


# @pytest.fixture(name="resource_uow")
# def fixture_resource_uow() -> InMemoryResourceUnitOfWork:
#     return InMemoryResourceUnitOfWork()


# @pytest.fixture(name="entry_uows")
# def fixture_entry_uows() -> repositories.EntriesUnitOfWork:
#     return repositories.EntriesUnitOfWork()


# @pytest.fixture(name="entry_uow_factory")
# def fixture_entry_uow_factory() -> InMemoryEntryUowFactory:
#     return InMemoryEntryUowFactory()


@pytest.fixture()
def lex_ctx() -> adapters.UnitTestContext:
    container = injector.Injector(
        [
            CommandBusMod(),
            EventBusMod(),
            Lex(),
            adapters.InMemoryLexInfrastructure(),
        ],
        auto_bind=False,
    )
    return adapters.UnitTestContext(
        container=container,
        command_bus=container.get(CommandBus),  # type: ignore [misc]
    )


@pytest.fixture()
def command_bus(unit_test_injector: injector.Injector) -> CommandBus:
    return unit_test_injector.get(CommandBus)  # type: ignore [misc]
