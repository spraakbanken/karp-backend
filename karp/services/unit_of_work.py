"""Unit of Work"""
import abc
from functools import singledispatch
import typing

from karp.domain import index, network, repository

RepositoryType = typing.TypeVar(
    "RepositoryType", repository.Repository, index.Index, network.Network
)


class UnitOfWork(typing.Generic[RepositoryType], abc.ABC):
    def __enter__(self) -> "UnitOfWork":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rollback()

    def commit(self):
        self._commit()

    def collect_new_events(self) -> typing.Iterable:
        for entity in self.repo.seen:
            while entity.events:
                yield entity.events.pop(0)

    @abc.abstractmethod
    def _commit(self):
        pass

    @abc.abstractmethod
    def rollback(self):
        pass

    @property
    @abc.abstractmethod
    def repo(self) -> RepositoryType:
        pass


class ResourceUnitOfWork(UnitOfWork[repository.ResourceRepository]):
    @property
    def resources(self) -> repository.ResourceRepository:
        return self.repo


class EntryUnitOfWork(UnitOfWork[repository.EntryRepository]):
    @property
    def entries(self) -> repository.EntryRepository:
        return self.repo


class IndexUnitOfWork(UnitOfWork[index.Index]):
    pass


class EntriesUnitOfWork(UnitOfWork):
    def __init__(self, entry_uows=None):
        self.entry_uows: typing.Dict[str, EntryUnitOfWork] = (
            {key: uow for key, uow in entry_uows} if entry_uows else {}
        )

    def get(self, resource_id: str) -> EntryUnitOfWork:
        return self.entry_uows[resource_id]

    @property
    def repo(self):
        return self

    def _commit(self):
        pass

    def rollback(self):
        pass


def unit_of_work(*, using, **kwargs) -> UnitOfWork:
    return create_unit_of_work(using, **kwargs)


@singledispatch
def create_unit_of_work(repo) -> UnitOfWork:
    class Dummy(UnitOfWork):
        def __enter__(self):
            raise NotImplementedError(f"Can't handle repository '{repo!r}'")

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    return Dummy()
