"""Unit of Work"""
import abc
from functools import singledispatch


class UnitOfWork(abc.ABC):
    @abc.abstractmethod
    def __enter__(self) -> "UnitOfWork":
        pass

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abc.abstractmethod
    def commit(self):
        pass

    @abc.abstractmethod
    def rollback(self):
        pass

    @property
    @abc.abstractmethod
    def repo(self):
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
