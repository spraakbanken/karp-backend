"""Unit of Work"""
import abc
from functools import singledispatch
from typing import Iterable

from karp.domain import repository


class UnitOfWork(abc.ABC):
    def __enter__(self) -> "UnitOfWork":
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rollback()

    def commit(self):
        self._commit()

    def collect_new_events(self) -> Iterable:
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
    def repo(self) -> repository.Repository:
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
