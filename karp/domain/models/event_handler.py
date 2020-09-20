"""Event handler."""
import collections
from typing import Callable, Dict, Set

from karp.domain.models.events import DomainEvent

EventPredicate = Callable[[DomainEvent], bool]
EventSubscriber = Callable[[DomainEvent], None]


class EventHandler:
    _event_handlers: Dict[EventPredicate, Set[EventSubscriber]]

    def __init__(self):
        self._event_handlers = collections.defaultdict(set)

    def subscribe(self, predicate: EventPredicate, subscriber: EventSubscriber):
        self._event_handlers[predicate].add(subscriber)

    def unsubscribe(self, predicate: EventPredicate, subscriber: EventSubscriber):
        if predicate in self._event_handlers:
            self._event_handlers[predicate].discard(subscriber)
            if len(self._event_handlers[predicate]) == 0:
                del self._event_handlers[predicate]

    def unsubscribe_all(self, subscriber: EventSubscriber):
        predicates_for_removal = []
        for predicate, subscribers in self._event_handlers.items():
            subscribers.discard(subscriber)
            if len(subscribers) == 0:
                predicates_for_removal.append(predicate)

        for predicate in predicates_for_removal:
            del self._event_handlers[predicate]

    def publish(self, event: DomainEvent):
        matching_handlers = set()

        for event_predicate, handlers in self._event_handlers.items():
            if event_predicate(event):
                matching_handlers.update(handlers)

        for handler in matching_handlers:
            handler(event)


_event_handler: EventHandler = EventHandler()


subscribe = _event_handler.subscribe


unsubscribe = _event_handler.unsubscribe


unsubscribe_all = _event_handler.unsubscribe_all


publish = _event_handler.publish
