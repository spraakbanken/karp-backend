import pytest

from karp.lex_infrastructure.sql import sql_unit_of_work

from karp.tests.unit.lex import factories


class TestSqlResourceUnitOfWork:
    def test_rolls_back_uncommitted_work_by_default(self, sqlite_session_factory):
        uow = sql_unit_of_work.SqlResourceUnitOfWork(sqlite_session_factory)
        with uow:
            resource = factories.ResourceFactory()
            uow.resources.save(resource)

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
