import injector
import pytest

from karp.foundation.commands import CommandBus
from karp.lex import Lex
from karp.lex.application.repositories import (
    EntryUowRepositoryUnitOfWork,
    EntryRepositoryUnitOfWorkFactory,
)
from karp.main.modules import CommandBusMod
from karp.lex.application import repositories

from .adapters import (
    FakeEntryUowRepositoryUnitOfWork,
    FakeEntryUowFactory,
    FakeResourceUnitOfWork,
    FakeSearchServiceUnitOfWork,
    FakeEntryRepositoryUnitOfWorkFactory,
)


@pytest.fixture(name="entry_repo_repo_uow")
def fixture_entry_repo_repo_uow() -> EntryUowRepositoryUnitOfWork:
    return FakeEntryUowRepositoryUnitOfWork()


@pytest.fixture(name="entry_repo_uow_factory")
def fixture_entry_repo_uow_factory() -> EntryRepositoryUnitOfWorkFactory:
    return FakeEntryRepositoryUnitOfWorkFactory()


def configure_for_testing(binder: injector.Binder) -> None:
    binder.bind(
        EntryRepositoryRepositoryUnitOfWork,
        to=FakeEntryRepositoryRepositoryUnitOfWork
    )


@pytest.fixture(name="resource_uow")
def fixture_resource_uow() -> FakeResourceUnitOfWork:
    return FakeResourceUnitOfWork()


@pytest.fixture(name="entry_uows")
def fixture_entry_uows() -> repositories.EntriesUnitOfWork:
    return repositories.EntriesUnitOfWork()


@pytest.fixture(name="entry_uow_factory")
def fixture_entry_uow_factory() -> FakeEntryUowFactory:
    return FakeEntryUowFactory()


@pytest.fixture()
def search_service_uow() -> FakeSearchServiceUnitOfWork:
    return FakeSearchServiceUnitOfWork()


@pytest.fixture()
def unit_test_injector() -> injector.Injector:
    return injector.Injector(
        [
            CommandBusMod(),
            Lex(),
            configure_for_tests
        ]
    )


@pytest.fixture()
def command_bus(unit_test_injector: injector.Injector) -> CommandBus:
    return unit_test_injector.get(CommandBus)
