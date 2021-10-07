from karp.foundation import repository

from .entries import EntryRepository


class EntryRepositoryRepository(repository.Repository[EntryRepository]):
    pass
