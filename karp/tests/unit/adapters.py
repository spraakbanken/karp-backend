from karp.domain import repository
from karp.infrastructure.unit_of_work import UnitOfWork, create_unit_of_work


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


class FakeUnitOfWork(UnitOfWork):
    def __init__(self, repo):
        self._repo = repo

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

    @property
    def repo(self):
        return self._repo


@create_unit_of_work.register(FakeEntryRepository)
def _(repo: FakeEntryRepository):
    return FakeUnitOfWork(repo)
