"""Pytest entry point."""

# pylint: disable=wrong-import-position,missing-function-docstring
from karp.main import AppContext
from karp.tests.integration.auth.adapters import create_bearer_token
from karp import auth, config
import os
import json
import typing
from typing import Any, Dict, Generator, Optional, Tuple

from fastapi import FastAPI
from typer import Typer
from typer.testing import CliRunner

import alembic
import alembic.config
from karp.foundation.value_objects import make_unique_id
from karp.foundation.commands import CommandBus
import elasticsearch_test  # pyre-ignore

import pytest  # pyre-ignore
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import session, sessionmaker
from starlette.testclient import TestClient

from alembic.config import main as alembic_main

# environ["TESTING"] = "True"
# environ["ELASTICSEARCH_HOST"] = "localhost:9202"
# environ["CONSOLE_LOG_LEVEL"] = "DEBUG"

# print("importing karp stuf ...")
from karp.tests import common_data, utils  # nopep8
from karp.auth_infrastructure import TestAuthInfrastructure  # nopep8
import karp.lex_infrastructure.sql.sql_models  # nopep8
from karp.db_infrastructure.db import metadata  # nopep8
from karp.lex.domain import commands, errors, entities  # nopep8
from karp import errors as karp_errors  # nopep8


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


@pytest.fixture(scope="session")
def setup_environment() -> None:
    os.environ["TESTING"] = "1"
    os.environ["AUTH_JWT_PUBKEY_PATH"] = "karp/tests/data/pubkey.pem"
    os.environ["ELASTICSEARCH_HOST"] = "localhost:9202"


@pytest.fixture(scope="session")
def apply_migrations(setup_environment: None):
    from karp.main.migrations import use_cases

    print("running alembic upgrade ...")
    uc = use_cases.RunningMigrationsUp()
    uc.execute(use_cases.RunMigrationsUp())
    yield


@pytest.fixture(scope="session", name="runner")
def fixture_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(scope="session", name="cliapp")
def fixture_cliapp() -> Typer:
    from karp.cliapp.main import create_app

    return create_app()


@pytest.fixture(name="app", scope="session")
def fixture_app(
    apply_migrations: None, init_search_service: None
) -> Generator[FastAPI, None, None]:
    from karp.webapp.main import create_app

    app = create_app()
    # app.state.app_context.container.binder.install(TestAuthInfrastructure())
    yield app
    print("dropping app")
    app = None


@pytest.fixture(name="app_context", scope="session")
def fixture_app_context(app: FastAPI) -> AppContext:
    return app.state.app_context


@pytest.fixture(name="fa_client", scope="session")
def fixture_client(app: FastAPI) -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


#     async with LifespanManager(app):
#         async with AsyncClient(
#             app=app,
#             base_url="http://testserver",
#             headers={"Content-Type": "application/json"}
#         ) as client:
#             yield client


def create_and_publish_resource(
    client: TestClient,
    *,
    path_to_config: str,
    access_token: auth.AccessToken,
) -> Tuple[bool, Optional[dict[str, Any]]]:
    from karp.webapp.schemas import ResourceCreate

    with open(path_to_config) as fp:
        resource_config = json.load(fp)

    resource_id = resource_config.pop("resource_id")
    resource = ResourceCreate(
        resource_id=resource_id,
        name=resource_config.pop("resource_name"),
        config=resource_config,
        message=f"{resource_id} added",
    )
    response = client.post(
        "/resources/",
        json=resource.dict(),
        headers=access_token.as_header(),
    )
    if response.status_code != 201:
        return False, {
            "error": f"Failed create resource: unexpected status_code: {response.status_code} != 201 ",
            "response.json": response.json(),
        }

    response = client.post(
        f"/resources/{resource_id}/publish",
        json={
            "message": f"{resource_id} published",
            "version": 1,
        },
        headers=access_token.as_header(),
    )
    if response.status_code != 200:
        return False, {
            "error": f"Failed publish resource: unexpected status_code: {response.status_code} != 200 ",
            "response.json": response.json(),
        }

    return True, None


@pytest.fixture(scope="session", name="fa_data_client")
def fixture_fa_data_client(
    fa_client,
    admin_token: auth.AccessToken,
):
    ok, msg = create_and_publish_resource(
        fa_client,
        path_to_config="karp/tests/data/config/places.json",
        access_token=admin_token,
    )
    assert ok, msg
    ok, msg = create_and_publish_resource(
        fa_client,
        path_to_config="karp/tests/data/config/municipalities.json",
        access_token=admin_token,
    )
    assert ok, msg
    utils.add_entries(
        fa_client,
        {"places": common_data.PLACES, "municipalities": common_data.MUNICIPALITIES},
        access_token=admin_token,
    )

    return fa_client


@pytest.fixture(scope="session")
def auth_levels() -> typing.Dict[str, int]:
    curr_level = 10
    levels = {}
    for level in auth.PermissionLevel:
        levels[level.value] = curr_level
        curr_level += 10

    return levels


@pytest.fixture(scope="session")
def user1_token(auth_levels: typing.Dict[str, int]) -> auth.AccessToken:
    return create_bearer_token(
        user="user1",
        levels=auth_levels,
        scope={
            "lexica": {
                "places": auth_levels[auth.PermissionLevel.write],
            }
        },
    )


@pytest.fixture(scope="session")
def user2_token(auth_levels: typing.Dict[str, int]) -> auth.AccessToken:
    return create_bearer_token(
        user="user2",
        levels=auth_levels,
        scope={
            "lexica": {
                "places": auth_levels[auth.PermissionLevel.write],
            }
        },
    )


@pytest.fixture(scope="session")
def user4_token(auth_levels: typing.Dict[str, int]) -> auth.AccessToken:
    return create_bearer_token(
        user="user4",
        levels=auth_levels,
        scope={
            "lexica": {
                "places": auth_levels[auth.PermissionLevel.admin],
            }
        },
    )


@pytest.fixture(scope="session")
def admin_token(auth_levels: typing.Dict[str, int]) -> auth.AccessToken:
    return create_bearer_token(
        user="alice@example.com",
        levels=auth_levels,
        scope={
            "lexica": {
                "places": auth_levels[auth.PermissionLevel.admin],
                "test_resource": auth_levels[auth.PermissionLevel.admin],
                "municipalities": auth_levels[auth.PermissionLevel.admin],
            }
        },
    )


@pytest.fixture(scope="session")
def read_token(auth_levels: typing.Dict[str, int]) -> auth.AccessToken:
    return create_bearer_token(
        user="bob@example.com",
        levels=auth_levels,
        scope={
            "lexica": {
                "places": auth_levels[auth.PermissionLevel.read],
                "test_resource": auth_levels[auth.PermissionLevel.read],
                "municipalities": auth_levels[auth.PermissionLevel.read],
            }
        },
    )


@pytest.fixture(scope="session")
def write_token(auth_levels: typing.Dict[str, int]) -> auth.AccessToken:
    return create_bearer_token(
        user="charlie@example.com",
        levels=auth_levels,
        scope={
            "lexica": {
                "places": auth_levels[auth.PermissionLevel.write],
                "test_resource": auth_levels[auth.PermissionLevel.write],
                "municipalities": auth_levels[auth.PermissionLevel.write],
            }
        },
    )


@pytest.fixture(name="init_search_service", scope="session")
def fixture_init_search_service():
    print("fixture: use_main_index")
    if not config.TEST_ELASTICSEARCH_ENABLED:
        print("don't use elasticsearch")
        # pytest.skip()
        yield
    else:
        if not config.TEST_ES_HOME:
            raise RuntimeError("must set ES_HOME to run tests that use elasticsearch")
        es_port = int(os.environ.get("TEST_ELASTICSEARCH_PORT", "9202"))
        with elasticsearch_test.ElasticsearchTest(
            port=es_port, es_path=config.TEST_ES_HOME
        ):
            yield


@pytest.fixture
def json_schema_config():
    return common_data.CONFIG_PLACES


# #
# #
# # @pytest.fixture(scope="session")
# # def client_with_entries_scope_session(es, client_with_data_f_scope_session):
# #     client_with_data = init(
# #         client_with_data_f_scope_session,
# #         es,
# #         {"places": PLACES, "municipalities": MUNICIPALITIES},
# #     )
# #     time.sleep(5)
# #     return client_with_data
