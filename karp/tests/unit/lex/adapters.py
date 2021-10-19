import dataclasses
import typing
from typing import Dict, List, Optional

import injector

from karp.foundation.value_objects import UniqueId
from karp.foundation.commands import CommandBus
from karp.lex.domain import entities as lex_entities
from karp.lex.application import repositories as lex_repositories
from karp.main.bootstrap import bootstrap_message_bus
from karp.tests.foundation.adapters import FakeUnitOfWork


@dataclasses.dataclass
class UnitTestContext:
    container: injector.Injector
    command_bus: CommandBus


class FakeResourceRepository(lex_repositories.ResourceRepository):
    def __init__(self):
        super().__init__()
        self.resources = {}

    def check_status(self):
        pass

    def _save(self, resource):
        self.resources[resource.id] = resource
    # def _update(self, resource):
    #     r = self._by_id(resource.id)
    #     self.resources.discard(r)
    #     self.resources.add(resource)

    def _by_id(self, id_, *, version=None):
        return self.resources.get(id_)

    def _by_resource_id(self, resource_id, *, version=None):
        return next((res for res in self.resources.values() if res.resource_id == resource_id), None)

    def __len__(self):
        return len(self.resources)

    def _get_published_resources(self) -> typing.Iterable[lex_entities.Resource]:
        return (res for res in self.resources if res.is_published)

    def resource_ids(self) -> typing.Iterable[str]:
        return (res.resource_id for res in self.resources)


class FakeEntryRepository(lex_repositories.EntryRepository):
    def __init__(self):
        super().__init__()
        self.entries = set()

    def check_status(self):
        pass

    def _save(self, entry):
        self.entries.add(entry)

    def _update(self, entry):
        r = self._by_id(entry.id)
        self.entries.discard(r)
        self.entries.add(entry)

    def _by_id(
        self,
        id,
        *,
        version=None,
        after_date=None,
        before_date=None,
        oldest_first=False,
    ):
        return next((r for r in self.entries if r.id == id), None)

    def _by_entry_id(
        self,
        entry_id,
        *,
        version=None,
        after_date=None,
        before_date=None,
    ):
        return next((r for r in self.entries if r.entry_id == entry_id), None)

    def __len__(self):
        return len(self.entries)

    def _create_repository_settings(self, *args):
        pass

    @classmethod
    def from_dict(cls, _):
        return cls()

    def all_entries(self) -> typing.Iterable[lex_entities.Entry]:
        yield from self.entries


class FakeEntryUnitOfWork(
    FakeUnitOfWork, lex_repositories.EntryUnitOfWork
):
    def __init__(self, entity_id, name: str, config: typing.Dict):
        self._entries = FakeEntryRepository()
        self.id = entity_id
        self.name = name
        self.config = config

    @property
    def repo(self) -> lex_repositories.EntryRepository:
        return self._entries


class FakeEntryUnitOfWork2(
    FakeUnitOfWork, lex_repositories.EntryUnitOfWork
):
    def __init__(self, entity_id, name: str, config: typing.Dict):
        self._entries = FakeEntryRepository()
        self.id = entity_id
        self.name = name
        self.config = config

    @property
    def repo(self) -> lex_repositories.EntryRepository:
        return self._entries


class FakeResourceUnitOfWork(FakeUnitOfWork, lex_repositories.ResourceUnitOfWork):
    def __init__(self):
        self._resources = FakeResourceRepository()

    @property
    def repo(self) -> lex_repositories.ResourceRepository:
        return self._resources


class FakeEntryUowFactory(lex_repositories.EntryUowFactory):
    def create(
        self,
        resource_id: str,
        resource_config: typing.Dict,
        entry_repository_settings,
    ) -> lex_repositories.EntryUnitOfWork:
        entry_uow = FakeEntryUnitOfWork(entry_repository_settings)
        if "entry_repository_type" in resource_config:
            entry_uow.repo.type = resource_config["entry_repository_type"]
        if entry_repository_settings:
            entry_uow.repo_settings = entry_repository_settings
        return entry_uow


class FakeEntryUnitOfWorkCreator:
    def __call__(
        self,
        entity_id: UniqueId,
        name: str,
        config: Dict,
    ) -> lex_repositories.EntryUnitOfWork:
        return FakeEntryUnitOfWork(
            entity_id=entity_id,
            name=name,
            config=config,
        )


def create_entry_uow2(
    entity_id: UniqueId,
    name: str,
    config: Dict,
) -> lex_repositories.EntryUnitOfWork:
    return FakeEntryUnitOfWork2(
        entity_id=entity_id,
        name=name,
        config=config,
    )


class FakeEntryUowRepository(lex_repositories.EntryUowRepository):
    def __init__(self) -> None:
        super().__init__()
        self._storage = {}

    def _save(self, entry_repo):
        self._storage[entry_repo.id] = entry_repo

    def _by_id(self, id_, *, version: Optional[int] = None):
        return self._storage.get(id_)

    def __len__(self):
        return len(self._storage)


class FakeEntryUowRepositoryUnitOfWork(FakeUnitOfWork, lex_repositories.EntryUowRepositoryUnitOfWork):
    def __init__(self) -> None:
        super().__init__()
        self._repo = FakeEntryUowRepository()

    @property
    def repo(self) -> lex_repositories.EntryRepositoryRepository:
        return self._repo


class FakeLexInfrastructure(injector.Module):
    @injector.provider
    @injector.singleton
    def entry_uow_repo_uow(self) -> lex_repositories.EntryUowRepositoryUnitOfWork:
        return FakeEntryUowRepositoryUnitOfWork()

    # @injector.provider
    # def entry_uow_factory(self) -> lex_repositories.EntryRepositoryUnitOfWorkFactory:
    #     return FakeEntryRepositoryUnitOfWorkFactory()
    @injector.multiprovider
    def entry_uow_creator_map(
        self
    ) -> Dict[str, lex_repositories.EntryUnitOfWorkCreator]:
        return {"fake": FakeEntryUnitOfWorkCreator(), "fake2": create_entry_uow2}

    @injector.provider
    @injector.singleton
    def resource_uow(self) -> lex_repositories.ResourceUnitOfWork:
        return FakeResourceUnitOfWork()


# def bootstrap_test_app(
#     resource_uow: lex_repositories.ResourceUnitOfWork = None,
#     entry_uows: lex_repositories.EntriesUnitOfWork = None,
#     entry_uow_factory: lex_repositories.EntryUowFactory = None,
#     search_service_uow: SearchServiceUnitOfWork = None,
#     entry_repo_repo_uow: lex_repositories.EntryRepositoryRepositoryUnitOfWork = None,
# ):
#     return bootstrap_message_bus(
#         resource_uow=resource_uow or FakeResourceUnitOfWork(),
#         entry_repo_repo_uow=entry_repo_repo_uow or FakeEntryRepositoryRepositoryUnitOfWork(),
#         entry_uows=entry_uows or lex_repositories.EntriesUnitOfWork(),
#         entry_uow_factory=entry_uow_factory or FakeEntryUowFactory(),
#         search_service_uow=search_service_uow or FakeSearchServiceUnitOfWork(),
#         raise_on_all_errors=True
#     )
