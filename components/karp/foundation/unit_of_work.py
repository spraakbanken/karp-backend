import abc
import logging
import typing
from karp.foundation import events

from karp.foundation.events import EventBus


RepositoryType = typing.TypeVar("RepositoryType")


logger = logging.getLogger(__name__)


class UnitOfWork(typing.Generic[RepositoryType], abc.ABC):
    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self._event_queue: list[events.Event] = []

    def __enter__(self):
        return self.begin()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rollback()
        self.close()

    def begin(self):
        return self

    def post_on_commit(self, events):
        if events is None:
            raise TypeError("expecting Iterable")
        self._event_queue.extend(events)

    def commit(self):
        logger.debug("called commit")
        self._commit()
        self._post_events()

    def _post_events(self):
        for event in self._event_queue:
            logger.debug("collecting events")
            self.event_bus.post(event)
        self._event_queue.clear()

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

    @abc.abstractmethod
    def _close(self):
        pass

    def close(self):
        self._close()
