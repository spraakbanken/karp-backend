import dataclasses
import typing
from typing import List
from karp import bootstrap
from karp.domain import index, repository, model
from karp.services import unit_of_work


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


class FakeEntryRepository(repository.EntryRepository, repository_type="fake"):
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

    def _by_id(self, id, *, version=None):
        return next((r for r in self.entries if r.id == id), None)

    def _by_entry_id(self, entry_id, *, version=None):
        return next((r for r in self.entries if r.entry_id == entry_id), None)

    def __len__(self):
        return len(self.entries)

    def _create_repository_settings(self, *args):
        pass

    @classmethod
    def from_dict(cls, _):
        return cls()


class FakeIndex(index.Index, index_type="fake"):
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
    FakeUnitOfWork, unit_of_work.EntryUnitOfWork, entry_repository_type="fake_entries"
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
    FakeUnitOfWork, unit_of_work.IndexUnitOfWork, index_type="fake_index"
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


def bootstrap_test_app(entry_uow_keys: List[str] = None):
    return bootstrap.bootstrap(
        resource_uow=FakeResourceUnitOfWork(),
        entry_uows=unit_of_work.EntriesUnitOfWork(
            # ((key, FakeEntryUnitOfWork()) for key in entry_uow_keys or [])
        ),
        index_uow=FakeIndexUnitOfWork(),
        entry_uow_factory=FakeEntryUowFactory(),
        raise_on_all_errors=True,
    )
