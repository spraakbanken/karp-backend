from karp.foundation import repository, unit_of_work, events
from karp.lex.domain import errors

from .entries import EntryRepository


class EntryUowRepository(repository.Repository):
    EntityNotFound = errors.EntryRepoNotFound
    pass


class EntryUowRepositoryUnitOfWork(unit_of_work.UnitOfWork[EntryUowRepository]):
    def __init__(self, event_bus: events.EventBus):
        unit_of_work.UnitOfWork.__init__(self, event_bus)

