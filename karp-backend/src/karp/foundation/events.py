import abc  # noqa: D100, I001
import logging
from typing import List, Generic, TypeVar, Any, Iterable

import injector
import logging  # noqa: F811


logger = logging.getLogger(__name__)


T = TypeVar("T")


class Event:  # noqa: D101
    pass


class EventMixin:  # noqa: D101
    def __init__(self) -> None:  # noqa: D107
        self._pending_domain_events: List[Event] = []

    def _record_event(self, event: Event) -> None:
        self._pending_domain_events.append(event)

    @property
    def domain_events(self) -> List[Event]:  # noqa: D102
        return self._pending_domain_events[:]

    def collect_new_events(self) -> Iterable[Event]:  # noqa: D102
        return self._pending_domain_events[:]

    def clear_events(self) -> None:  # noqa: D102
        self._pending_domain_events.clear()


class EventHandler(Generic[T]):
    """Simple generic used to associate handlers with events using DI.

    e.g EventHandler[ResourceCreated].
    """

    def __call__(self, event: T, *args: Any, **kwds: Any) -> Any:  # noqa: D102, ANN401
        raise NotImplementedError()


class EventBus(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def post(self, event: Event) -> None:  # noqa: D102
        raise NotImplementedError


class InjectorEventBus(EventBus):  # noqa: D101
    def __init__(self, container: injector.Injector) -> None:  # noqa: D107
        self._container = container

    def post(self, event: Event) -> None:  # noqa: D102
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
                except Exception as err:  # noqa: F841
                    logger.exception(
                        "Exception handling event", extra={"karp_event": event}
                    )
                    raise
