import abc
import typing

from karp.foundation.events import EventBus


RepositoryType = typing.TypeVar("RepositoryType")


class UnitOfWork(typing.Generic[RepositoryType], abc.ABC):
    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rollback()

    def commit(self):
        print('karp.foundation.UnitOfWork.commit')
        self._commit()
        for event in self.collect_new_events():
            self.event_bus.post(event)

    def collect_new_events(self) -> typing.Iterable:
        print(f'collect_new_events for unit_of_work {type(self)}')
        for entity in self.repo.seen:
            print(f'  from entity ({type(entity)}) with id {entity.id}')
            # yield from entity.domain_events
            yield from entity.collect_new_events()
            entity.clear_events()

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
