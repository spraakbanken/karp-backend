import pytest

from karp.services import unit_of_work

from .adapters import FakeEntryUowFactory, FakeResourceUnitOfWork


@pytest.fixture(name="resource_uow")
def fixture_resource_uow() -> FakeResourceUnitOfWork:
    return FakeResourceUnitOfWork()


@pytest.fixture(name="entry_uows")
def fixture_entry_uows() -> unit_of_work.EntriesUnitOfWork:
    return unit_of_work.EntriesUnitOfWork()


@pytest.fixture(name="entry_uow_factory")
def fixture_entry_uow_factory() -> FakeEntryUowFactory:
    return FakeEntryUowFactory()
