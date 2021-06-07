import pytest

from karp.domain import model
from karp.infrastructure.sql import sql_unit_of_work
from karp.utility import unique_id


def random_resource() -> model.Resource:
    return model.Resource(
        entity_id=unique_id.make_unique_id(),
        resource_id="abc",
        name="ABC",
        config={"fields": {}},
        message="added",
    )


def random_entry(resource_id: str = None) -> model.Entry:
    return model.Entry(
        entity_id=unique_id.make_unique_id(),
        entry_id="abc..1",
        resource_id=resource_id or "abc",
        body={"id": "abc..1"},
        message="added",
    )


class TestSqlResourceUnitOfWork:
    def test_rolls_back_uncommitted_work_by_default(self, sqlite_session_factory):
        uow = sql_unit_of_work.SqlResourceUnitOfWork(sqlite_session_factory)
        with uow:
            resource = random_resource()
            uow.resources.put(resource)

        new_session = sqlite_session_factory()
        rows = list(new_session.execute('SELECT * FROM "resources"'))
        assert rows == []

    def test_rolls_back_on_error(self, sqlite_session_factory):
        class MyException(Exception):
            pass

        uow = sql_unit_of_work.SqlResourceUnitOfWork(sqlite_session_factory)
        with pytest.raises(MyException):
            with uow:
                resource = random_resource()
                uow.resources.put(resource)
                raise MyException()

        new_session = sqlite_session_factory()
        rows = list(new_session.execute('SELECT * FROM "resources"'))
        assert rows == []


class TestSqlEntryUnitOfWork:
    def test_rolls_back_uncommitted_work_by_default(self, sqlite_session_factory):
        uow = sql_unit_of_work.SqlEntryUnitOfWork(
            {"resource_id": "abc", "table_name": "abc"},
            resource_config={"resource_id": "abc", "config": {}},
            session_factory=sqlite_session_factory,
        )
        with uow:
            entry = random_entry(resource_id="abc")
            uow.entries.put(entry)

        new_session = sqlite_session_factory()
        rows = list(new_session.execute('SELECT * FROM "resources"'))
        assert rows == []

    def test_rolls_back_on_error(self, sqlite_session_factory):
        class MyException(Exception):
            pass

        uow = sql_unit_of_work.SqlEntryUnitOfWork(
            {"resource_id": "abc", "table_name": "abc"},
            resource_config={"resource_id": "abc", "config": {}},
            session_factory=sqlite_session_factory,
        )
        with pytest.raises(MyException):
            with uow:
                entry = random_entry(resource_id="abc")
                uow.entries.put(entry)
                raise MyException()

        new_session = sqlite_session_factory()
        rows = list(new_session.execute('SELECT * FROM "resources"'))
        assert rows == []
