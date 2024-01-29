from karp.lex_infrastructure.repositories import SqlEntryUowRepository
from karp.foundation.events import EventBus, Event


class InMemoryEventBus(EventBus):
    def __init__(self) -> None:
        super().__init__()
        self.events: list[Event] = []

    def post(self, event: Event) -> None:
        self.events.append(event)


def test_create_sql_entry_uow_repo(sqlite_session_factory):  # noqa: ANN201
    session = sqlite_session_factory()

    repo = SqlEntryUowRepository(session=session, event_bus=InMemoryEventBus())  # noqa: F841
