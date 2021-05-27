from karp.domain.ports import ResourceRepository
from karp.infrastructure.unit_of_work import UnitOfWork


class FakeResourceRepository(ResourceRepository):

    def __init__(self):
        self.resources = []

    def add(self, resource):
        self.resources.append(resource)

    def get(self, id):
        return self.resources[id]

    def __len__(self):
        return len(self.resources)

    def __getitem__(self, idx):
        return self.resources[idx]


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

    def __exit__(self, type, value, traceback):
        self.exn_type = type
        self.exn = value
        self.traceback = traceback

    def commit(self):
        self.was_committed = True

    def rollback(self):
        self.was_rolled_back = True

    @property
    def repo(self):
        return self._repo
