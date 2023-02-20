import pytest  # noqa: I001

from karp.lex_core.value_objects import make_unique_id
from karp.foundation.events import EventBus, Event

from karp.lex_infrastructure.repositories import SqlResourceUnitOfWork
from karp.lex_infrastructure.repositories.sql_entries import SqlEntryUnitOfWork

from karp.tests.unit.lex import adapters, factories  # noqa: F401


class InMemoryEventBus(EventBus):
    def __init__(self) -> None:
        super().__init__()
        self.events: list[Event] = []

    def post(self, event: Event) -> None:
        self.events.append(event)


class TestSqlResourceUnitOfWork:
    def test_rolls_back_uncommitted_work_by_default(  # noqa: ANN201
        self, sqlite_session_factory
    ):
        uow = SqlResourceUnitOfWork(
            session_factory=sqlite_session_factory, event_bus=InMemoryEventBus()
        )
        with uow:
            resource = factories.ResourceFactory()
            uow.resources.save(resource)

        new_session = sqlite_session_factory()
        rows = list(new_session.execute('SELECT * FROM "resources"'))
        assert not rows

    def test_rolls_back_on_error(self, sqlite_session_factory):  # noqa: ANN201
        def do_something_that_fails(resource):  # noqa: ANN202
            print(resource.to_string())

        uow = SqlResourceUnitOfWork(
            session_factory=sqlite_session_factory, event_bus=InMemoryEventBus()
        )
        with pytest.raises(AttributeError):
            with uow:
                resource = factories.ResourceFactory()
                uow.resources.save(resource)
                do_something_that_fails(resource)

        new_session = sqlite_session_factory()
        rows = list(new_session.execute('SELECT * FROM "resources"'))
        assert not rows


class MyException(Exception):
    pass


class TestSqlEntryUnitOfWork:
    def test_rolls_back_uncommitted_work_by_default(  # noqa: ANN201
        self, sqlite_session_factory
    ):
        uow = SqlEntryUnitOfWork(
            # {"resource_id": "abc", "table_name": "abc"},
            # resource_config={"resource_id": "abc", "config": {}},
            sqlite_session_factory,
            event_bus=InMemoryEventBus(),
            name="test",
            config={},
            connection_str=":memory:",
            message="test message",
            id=make_unique_id(),
        )
        with uow:
            entry = factories.EntryFactory()  # resource_id="abc")
            uow.entries.save(entry)

        new_session = sqlite_session_factory()
        rows = list(new_session.execute('SELECT * FROM "test"'))
        assert not rows

    def test_rolls_back_on_error(self, sqlite_session_factory):  # noqa: ANN201
        uow = SqlEntryUnitOfWork(
            # {"resource_id": "abc", "table_name": "abc"},
            # resource_config={"resource_id": "abc", "config": {}},
            sqlite_session_factory,
            event_bus=InMemoryEventBus(),
            name="test",
            config={},
            connection_str=":memory:",
            message="test message",
            id=make_unique_id(),
        )
        with pytest.raises(MyException):
            with uow:
                entry = factories.EntryFactory()
                uow.entries.save(entry)
                do_something_that_fails()

        new_session = sqlite_session_factory()
        rows = list(new_session.execute('SELECT * FROM "test"'))
        assert not rows


def do_something_that_fails() -> None:
    raise MyException()
