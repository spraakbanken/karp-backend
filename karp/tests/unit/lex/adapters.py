import dataclasses
import typing
from typing import Dict, List, Optional

import injector

from karp.foundation.value_objects import UniqueId
from karp.foundation.commands import CommandBus
from karp.lex.domain import entities as lex_entities
from karp.lex.application import repositories as lex_repositories
from karp.main.bootstrap import bootstrap_message_bus
from karp.search.application.unit_of_work import SearchServiceUnitOfWork
from karp.search.domain import search_service


@dataclasses.dataclass
class UnitTestContext:
    container: injector.Injector
    command_bus: CommandBus


class FakeResourceRepository(lex_repositories.ResourceRepository):
    def __init__(self):
        super().__init__()
        self.resources = set()

    def check_status(self):
        pass

    def _save(self, resource):
        self.resources.add(resource)

    def _update(self, resource):
        r = self._by_id(resource.id)
        self.resources.discard(r)
        self.resources.add(resource)

    def _by_id(self, id, *, version=None):
        return next((r for r in self.resources if r.id == id), None)

    def _by_resource_id(self, resource_id, *, version=None):
        return next((r for r in self.resources if r.resource_id == resource_id), None)

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


class FakeSearchService(search_service.SearchService):
    @dataclasses.dataclass
    class Index:
        config: typing.Dict
        entries: typing.Dict[str, search_service.IndexEntry] = dataclasses.field(
            default_factory=dict
        )
        created: bool = True
        published: bool = False

    def __init__(self) -> None:
        super().__init__()
        self.indicies = {}
        self.seen = []

    def create_index(self, resource_id: str, config: typing.Dict):
        self.indicies[resource_id] = FakeSearchService.Index(config=config)

    def publish_index(self, alias_name: str, index_name: str = None):
        self.indicies[alias_name].published = True

    def add_entries(self, resource_id: str, entries: typing.List[search_service.IndexEntry]):
        for entry in entries:
            self.indicies[resource_id].entries[entry.id] = entry

    def delete_entry(
        self,
        resource_id: str,
        *,
        entry_id: typing.Optional[str],
        # entry: typing.Optional[model.Entry]
    ):
        del self.indicies[resource_id].entries[entry_id]

    def search_ids(self, resource_id: str, entry_ids: str):
        return {}

    def query(self, request: search_service.QueryRequest):
        return {}

    def query_split(self, request: search_service.QueryRequest):
        return {}

    def statistics(self, resource_id: str, field: str):
        return {}


class FakeUnitOfWork:
    def start(self):
        self.was_committed = False
        self.was_rolled_back = False
        return self

    def __enter__(self):
        self.was_committed = False
        self.was_rolled_back = False
        return self

    # def __exit__(self, type, value, traceback):
    #     self.exn_type = type
    #     self.exn = value
    #     self.traceback = traceback

    def _commit(self):
        self.was_committed = True

    def rollback(self):
        self.was_rolled_back = True


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


class FakeResourceUnitOfWork(FakeUnitOfWork, lex_repositories.ResourceUnitOfWork):
    def __init__(self):
        self._resources = FakeResourceRepository()

    @property
    def repo(self) -> lex_repositories.ResourceRepository:
        return self._resources


class FakeSearchServiceUnitOfWork(
    FakeUnitOfWork, SearchServiceUnitOfWork
):
    def __init__(self):
        self._index = FakeSearchService()

    @property
    def repo(self) -> search_service.SearchService:
        return self._index


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


class FakeEntryRepositoryUnitOfWorkFactory(
    lex_repositories.EntryRepositoryUnitOfWorkFactory
):
    def create(
        self,
        repository_type: str,
        entity_id: UniqueId,
        name: str,
        config: Dict,
    ) -> lex_repositories.EntryUnitOfWork:
        return FakeEntryUnitOfWork(
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

    @injector.provider
    def entry_uow_factory(self) -> lex_repositories.EntryRepositoryUnitOfWorkFactory:
        return FakeEntryRepositoryUnitOfWorkFactory()

    @injector.provider
    @injector.singleton
    def resource_uow(self) -> lex_repositories.ResourceUnitOfWork:
        return FakeResourceUnitOfWork()


def bootstrap_test_app(
    resource_uow: lex_repositories.ResourceUnitOfWork = None,
    entry_uows: lex_repositories.EntriesUnitOfWork = None,
    entry_uow_factory: lex_repositories.EntryUowFactory = None,
    search_service_uow: SearchServiceUnitOfWork = None,
    entry_repo_repo_uow: lex_repositories.EntryRepositoryRepositoryUnitOfWork = None,
):
    return bootstrap_message_bus(
        resource_uow=resource_uow or FakeResourceUnitOfWork(),
        entry_repo_repo_uow=entry_repo_repo_uow or FakeEntryRepositoryRepositoryUnitOfWork(),
        entry_uows=entry_uows or lex_repositories.EntriesUnitOfWork(),
        entry_uow_factory=entry_uow_factory or FakeEntryUowFactory(),
        search_service_uow=search_service_uow or FakeSearchServiceUnitOfWork(),
        raise_on_all_errors=True
    )
