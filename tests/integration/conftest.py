"""Pytest entry point."""


import injector
import pytest  # pyre-ignore  # noqa: F811
from sqlalchemy import create_engine
from sqlalchemy.orm import session, sessionmaker

from alembic.config import main as alembic_main  # noqa: F401

from tests.unit.lex.adapters import InMemoryLexInfrastructure


# environ["TESTING"] = "True"
# environ["ELASTICSEARCH_HOST"] = "localhost:9202"
# environ["CONSOLE_LOG_LEVEL"] = "DEBUG"

from karp.db_infrastructure.db import metadata  # nopep8
from tests.unit.search import adapters as search_adapters
from tests.integration import adapters


@pytest.fixture(name="in_memory_sqlite_db")
def fixture_in_memory_sqlite_db():  # noqa: ANN201
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    yield engine
    session.close_all_sessions()
    metadata.drop_all(bind=engine)


@pytest.fixture
def sqlite_session_factory(in_memory_sqlite_db):  # noqa: ANN201
    yield sessionmaker(bind=in_memory_sqlite_db)


@pytest.fixture()
def integration_ctx() -> adapters.IntegrationTestContext:
    container = injector.Injector(
        [
            InMemoryLexInfrastructure(),
            search_adapters.InMemorySearchInfrastructure(),
        ]
    )
    return adapters.IntegrationTestContext(
        container=container,
    )
