import abc
import typing

RepositoryType = typing.TypeVar("RepositoryType")


class UnitOfWork(typing.Generic[RepositoryType], abc.ABC):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rollback()

    def commit(self):
        print('karp.foundation.UnitOfWork.commit')
        self._commit()

    def collect_new_events(self) -> typing.Iterable:
        for entity in self.repo.seen:
            while entity.events:
                yield entity.events.pop(0)

    @abc.abstractmethod
    def _commit(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def rollback(self):
        pass

    @property
    @abc.abstractmethod
    def repo(self) -> RepositoryType:
        pass
