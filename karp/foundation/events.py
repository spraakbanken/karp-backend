from typing import List


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

    def clear_events(self) -> None:
        self._pending_domain_events.clear()
