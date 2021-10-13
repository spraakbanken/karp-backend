from karp.foundation import repository, unit_of_work

from .entries import EntryRepository


class EntryRepositoryRepository(repository.Repository[EntryRepository]):
    pass


class EntryUowRepository(repository.Repository):
    pass


class EntryUowRepositoryUnitOfWork(unit_of_work.UnitOfWork[EntryUowRepository]):
    pass
