import factory
import pytest

from karp.foundation.commands import CommandBus
from karp.lex.application.handlers import (
    CreateEntryRepositoryHandler,
)
from karp.lex.domain.commands import CreateEntryRepository
from karp.lex.domain.value_objects.factories import make_unique_id

from karp.tests.unit.adapters import (
    FakeEntryUowRepositoryUnitOfWork,
    FakeEntryRepositoryUnitOfWorkFactory,
)


class CreateEntryRepositoryFactory(factory.Factory):
    class Meta:
        model = CreateEntryRepository

    entity_id = factory.LazyFunction(make_unique_id)
    name = factory.Faker('word')
    repository_type = 'fake'
    config = {}


@pytest.fixture(name='create_entry_repository')
def fixture_create_entry_repository() -> CreateEntryRepository:
    return CreateEntryRepositoryFactory()


class TestCreateEntryRepository:
    def test_create_entry_repository(
        self,
        create_entry_repository: CreateEntryRepository,
        entry_repo_repo_uow: FakeEntryUowRepositoryUnitOfWork,
        entry_repo_uow_factory: FakeEntryRepositoryUnitOfWorkFactory,
    ):
        cmd_handler = CreateEntryRepositoryHandler(
            entry_repo_repo_uow,
            entry_repo_uow_factory,
        )
        cmd_handler(create_entry_repository)

        assert entry_repo_repo_uow.was_committed
        assert len(entry_repo_repo_uow.repo) == 1
