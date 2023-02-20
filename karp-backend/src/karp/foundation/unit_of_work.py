import abc  # noqa: D100, I001
import logging
import typing
from karp.foundation import events

from karp.foundation.events import EventBus


RepositoryType = typing.TypeVar("RepositoryType")


logger = logging.getLogger(__name__)


class UnitOfWork(typing.Generic[RepositoryType], abc.ABC):  # noqa: D101
    def __init__(self, event_bus: EventBus) -> None:  # noqa: D107
        self.event_bus = event_bus
        self._event_queue: list[events.Event] = []

    def __enter__(self):  # noqa: ANN204, D105
        return self.begin()

    def __exit__(self, exc_type, exc_val, exc_tb):  # noqa: ANN204, D105
        self.rollback()
        self.close()

    def begin(self):  # noqa: ANN201, D102
        return self

    def post_on_commit(self, events):  # noqa: ANN201, D102
        if events is None:
            raise TypeError("expecting Iterable")
        self._event_queue.extend(events)

    def commit(self):  # noqa: ANN201, D102
        logger.debug("called commit")
        self._commit()
        self._post_events()

    def _post_events(self):  # noqa: ANN202
        for event in self._event_queue:
            logger.debug("collecting events")
            self.event_bus.post(event)
        self._event_queue.clear()

    @abc.abstractmethod
    def _commit(self):  # noqa: ANN202
        raise NotImplementedError()

    @abc.abstractmethod
    def rollback(self):  # noqa: ANN201, D102
        pass

    @property
    @abc.abstractmethod
    def repo(self) -> RepositoryType:  # noqa: D102
        pass

    @abc.abstractmethod
    def _close(self):  # noqa: ANN202
        pass

    def close(self):  # noqa: ANN201, D102
        self._close()
