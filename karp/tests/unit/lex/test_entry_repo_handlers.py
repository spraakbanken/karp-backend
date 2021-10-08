import factory
import pytest

from karp.foundation.commands import CommandBus
from karp.lex.application.handlers import (
    CreateEntryRepositoryHandler,
)
from karp.lex.domain.commands import CreateEntryRepository
from karp.lex.domain.value_objects.factories import make_unique_id

from karp.tests.unit.adapters import bootstrap_test_app, FakeEntryRepositoryRepositoryUnitOfWork


class CreateEntryRepositoryFactory(factory.Factory):
    class Meta:
        model = CreateEntryRepository

    entity_id = factory.LazyFunction(make_unique_id)


@pytest.fixture(name='create_entry_repository')
def fixture_create_entry_repository() -> CreateEntryRepository:
    return CreateEntryRepositoryFactory()


class TestCreateEntryRepository:
    def test_create_entry_repository(
        self,
        create_entry_repository: CreateEntryRepository,
        entry_repo_repo_uow: FakeEntryRepositoryRepositoryUnitOfWork,
    ):
        cmd_handler = CreateEntryRepositoryHandler(entry_repo_repo_uow)
        cmd_handler(create_entry_repository)

        assert len(entry_repo_repo_uow.repo) == 1
