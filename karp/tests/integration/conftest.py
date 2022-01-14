"""Pytest entry point."""


import pytest  # pyre-ignore
from sqlalchemy import create_engine
from sqlalchemy.orm import session, sessionmaker

from alembic.config import main as alembic_main

# environ["TESTING"] = "True"
# environ["ELASTICSEARCH_HOST"] = "localhost:9202"
# environ["CONSOLE_LOG_LEVEL"] = "DEBUG"

from karp.db_infrastructure.db import metadata  # nopep8


@pytest.fixture(name="in_memory_sqlite_db")
def fixture_in_memory_sqlite_db():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    yield engine
    session.close_all_sessions()
    metadata.drop_all(bind=engine)


@pytest.fixture
def sqlite_session_factory(in_memory_sqlite_db):
    yield sessionmaker(bind=in_memory_sqlite_db)
