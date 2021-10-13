from karp.foundation import repository, unit_of_work
from karp.lex.domain import errors

from .entries import EntryRepository


class EntryRepositoryRepository(repository.Repository[EntryRepository]):
    EntityNotFound = errors.EntryRepoNotFound
    pass


class EntryUowRepository(repository.Repository):
    EntityNotFound = errors.EntryRepoNotFound
    pass


class EntryUowRepositoryUnitOfWork(unit_of_work.UnitOfWork[EntryUowRepository]):
    pass
