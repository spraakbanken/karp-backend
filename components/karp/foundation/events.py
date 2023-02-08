import abc
import logging
from typing import List, Generic, TypeVar, Any, Iterable

import injector
import logging


logger = logging.getLogger(__name__)


T = TypeVar("T")


class Event:
    pass


class EventMixin:
    def __init__(self) -> None:
        self._pending_domain_events: List[Event] = []

    def _record_event(self, event: Event) -> None:
        self._pending_domain_events.append(event)

    @property
    def domain_events(self) -> List[Event]:
        return self._pending_domain_events[:]

    def collect_new_events(self) -> Iterable[Event]:
        return self._pending_domain_events[:]

    def clear_events(self) -> None:
        self._pending_domain_events.clear()


class EventHandler(Generic[T]):
    """Simple generic used to associate handlers with events using DI.

    e.g EventHandler[ResourceCreated].
    """

    def __call__(self, event: T, *args: Any, **kwds: Any) -> Any:
        raise NotImplementedError()


class EventBus(abc.ABC):
    @abc.abstractmethod
    def post(self, event: Event) -> None:
        raise NotImplementedError


class InjectorEventBus(EventBus):
    def __init__(self, container: injector.Injector) -> None:
        self._container = container

    def post(self, event: Event) -> None:
        logger.info("handling event", extra={"karp_event": event})
        try:
            evt_handlers = self._container.get(
                List[EventHandler[type(event)]]  # type: ignore
            )
        except injector.UnsatisfiedRequirement as err:
            logger.info(
                "No event handler for event?",
                extra={"karp_event": event, "err_message": err},
            )
        else:
            for evt_handler in evt_handlers:
                logger.debug(
                    "handling event with handler",
                    extra={"karp_event": event, "evt_handler": evt_handler},
                )
                try:
                    evt_handler(event)
                except Exception as err:
                    logger.exception(
                        "Exception handling event", extra={"karp_event": event}
                    )
                    raise
