import dataclasses
import typing
from typing import List

from karp.domain import index, model, repository
from karp.lex.application import unit_of_work as lex_unit_of_work, repositories as lex_repositories
from karp.main.bootstrap import bootstrap_message_bus
from karp.services import unit_of_work
from karp.search.application.unit_of_work import SearchServiceUnitOfWork


class FakeResourceRepository(repository.ResourceRepository):
    def __init__(self):
        super().__init__()
        self.resources = set()

    def check_status(self):
        pass

    def _put(self, resource):
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

    def _get_published_resources(self) -> typing.Iterable[model.Resource]:
        return (res for res in self.resources if res.is_published)

    def resource_ids(self) -> typing.Iterable[str]:
        return (res.resource_id for res in self.resources)


class FakeEntryRepository(repository.EntryRepository):
    def __init__(self):
        super().__init__()
        self.entries = set()

    def check_status(self):
        pass

    def _put(self, entry):
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

    def all_entries(self) -> typing.Iterable[model.Entry]:
        yield from self.entries


class FakeIndex(index.Index):
    @dataclasses.dataclass
    class Index:
        config: typing.Dict
        entries: typing.Dict[str, index.IndexEntry] = dataclasses.field(
            default_factory=dict
        )
        created: bool = True
        published: bool = False

    def __init__(self) -> None:
        super().__init__()
        self.indicies = {}
        self.seen = []

    def create_index(self, resource_id: str, config: typing.Dict):
        self.indicies[resource_id] = FakeIndex.Index(config=config)

    def publish_index(self, alias_name: str, index_name: str = None):
        self.indicies[alias_name].published = True

    def add_entries(self, resource_id: str, entries: typing.List[index.IndexEntry]):
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

    def query(self, request: index.QueryRequest):
        return {}

    def query_split(self, request: index.QueryRequest):
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
    FakeUnitOfWork, unit_of_work.EntryUnitOfWork
):
    def __init__(self, settings: typing.Dict):
        self._entries = FakeEntryRepository()
        self.repo_settings = settings

    @property
    def repo(self) -> repository.EntryRepository:
        return self._entries


class FakeResourceUnitOfWork(FakeUnitOfWork, unit_of_work.ResourceUnitOfWork):
    def __init__(self):
        self._resources = FakeResourceRepository()

    @property
    def repo(self) -> repository.ResourceRepository:
        return self._resources


class FakeIndexUnitOfWork(
    FakeUnitOfWork, unit_of_work.IndexUnitOfWork
):
    def __init__(self):
        self._index = FakeIndex()

    @property
    def repo(self) -> index.Index:
        return self._index


class FakeSearchServiceUnitOfWork(
    FakeUnitOfWork, unit_of_work.IndexUnitOfWork
):
    def __init__(self):
        self._index = FakeIndex()

    @property
    def repo(self) -> index.Index:
        return self._index


class FakeEntryUowFactory(unit_of_work.EntryUowFactory):
    def create(
        self,
        resource_id: str,
        resource_config: typing.Dict,
        entry_repository_settings,
    ) -> unit_of_work.EntryUnitOfWork:
        entry_uow = FakeEntryUnitOfWork(entry_repository_settings)
        if "entry_repository_type" in resource_config:
            entry_uow.repo.type = resource_config["entry_repository_type"]
        if entry_repository_settings:
            entry_uow.repo_settings = entry_repository_settings
        return entry_uow


class FakeEntryRepositoryRepository(lex_repositories.EntryRepositoryRepository):
    def __init__(self) -> None:
        super().__init__()


class FakeEntryRepositoryRepositoryUnitOfWork(FakeUnitOfWork, lex_unit_of_work.EntryRepositoryRepositoryUnitOfWork):
    def __init__(self) -> None:
        super().__init__()
        self._repo = FakeEntryRepositoryRepository()

    @property
    def repo(self) -> lex_repositories.EntryRepositoryRepository:
        return self._repo


def bootstrap_test_app(
    resource_uow: unit_of_work.ResourceUnitOfWork = None,
    entry_uows: unit_of_work.EntriesUnitOfWork = None,
    entry_uow_factory: unit_of_work.EntryUowFactory = None,
    search_service_uow: SearchServiceUnitOfWork = None,
    entry_repo_repo_uow: lex_unit_of_work.EntryRepositoryRepositoryUnitOfWork = None,
):
    return bootstrap_message_bus(
        resource_uow=resource_uow or FakeResourceUnitOfWork(),
        entry_repo_repo_uow=entry_repo_repo_uow or FakeEntryRepositoryRepositoryUnitOfWork(),
        entry_uows=entry_uows or unit_of_work.EntriesUnitOfWork(),
        entry_uow_factory=entry_uow_factory or FakeEntryUowFactory(),
        search_service_uow=search_service_uow or FakeSearchServiceUnitOfWork(),
        raise_on_all_errors=True
    )
