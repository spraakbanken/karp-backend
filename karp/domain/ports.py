import abc

from .model import Resource


class ResourceRepository(abc.ABC):

    @abc.abstractmethod
    def add(self, resource: Resource) -> None:
        pass


class UnitOfWork(abc.ABC):

    @abc.abstractmethod
    def __enter__(self):
        pass

    @abc.abstractmethod
    def __exit__(self, type, value, traceback):
        pass

    @abc.abstractmethod
    def commit(self):
        pass

    @abc.abstractmethod
    def rollback(self):
        pass

    @property
    @abc.abstractmethod
    def resources(self):
        pass


class UnitOfWorkManager(abc.ABC):

    @abc.abstractmethod
    def start(self) -> UnitOfWork:
        pass
