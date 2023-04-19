"""Pytest entry point."""
from karp.command_bus import CommandBus
from karp.lex import commands
from karp.main import AppContext
from tests.integration.auth.adapters import create_bearer_token
from karp import auth
import os
import json
import typing
from typing import Any, Generator, Optional, Tuple

from fastapi import FastAPI
from typer import Typer
from typer.testing import CliRunner

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import session, sessionmaker
from starlette.testclient import TestClient

from tests import common_data, utils
from karp.db_infrastructure.db import metadata


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


@pytest.fixture(scope="session")
def setup_environment() -> None:
    os.environ["TESTING"] = "1"
    os.environ["AUTH_JWT_PUBKEY_PATH"] = "assets/testing/pubkey.pem"
    os.environ["ELASTICSEARCH_HOST"] = "localhost:9202"


@pytest.fixture(scope="session")
def apply_migrations(setup_environment: None):  # noqa: ANN201
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
    from karp.karp_v6_api.main import create_app

    yield create_app()
    print("dropping app")
    app = None  # noqa: F841


@pytest.fixture(name="app_context", scope="session")
def fixture_app_context(app: FastAPI) -> AppContext:
    return app.state.app_context


@pytest.fixture(name="fa_client", scope="session")
def fixture_client(app: FastAPI) -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


def create_and_publish_resource(
    client: TestClient,
    *,
    path_to_config: str,
) -> Tuple[bool, Optional[dict[str, Any]]]:

    with open(path_to_config) as fp:
        resource_config = json.load(fp)

    resource_id = resource_config.pop("resource_id")

    command_bus = client.app.state.app_context.container.get(CommandBus)

    entry_repo = command_bus.dispatch(
            commands.CreateEntryRepository(
                name=resource_id,
                config=resource_config,
                user="",
                message="",
            )
    )

    create_resource = commands.CreateResource(
        resourceId=resource_id,
        user="",
        name=resource_config.pop("resource_name"),
        config=resource_config,
        message=f"{resource_id} added",
        entryRepoId=entry_repo.entity_id
    )

    command_bus.dispatch(create_resource)

    publish_resource = commands.PublishResource(
        user="",
        resourceId=resource_id,
        version=1
    )

    command_bus.dispatch(publish_resource)


@pytest.fixture(scope="session", name="fa_data_client")
def fixture_fa_data_client(  # noqa: ANN201
    fa_client,
    admin_token: auth.AccessToken,
):
    create_and_publish_resource(
        fa_client,
        path_to_config="assets/testing/config/places.json",
    )
    create_and_publish_resource(
        fa_client,
        path_to_config="assets/testing/config/municipalities.json",
    )
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
def fixture_init_search_service():  # noqa: ANN201
    # TODO this does not work right know, to test the e2e tests
    # Stop any running instances of ES to avoid data loss and clusters forming
    # run `elasticsearch -Ehttp.port=9202`
    # replace the exception in this function with "yield"
    # NOTE: after each test run the indices in ES must be removed manually :(
    #      `curl -XDELETE localhost:9202/*` or remove the data folder and restart
    # raise Exception("You must manually start Elasticsearch, see tests/e2e/conftest.py")
    # this is how it should be done, but for some reason it does not work and it also forms a cluster
    # with any running node when starting
    # if not config("TEST_ES_HOME"):
    #     raise RuntimeError("must set ES_HOME to run tests that use elasticsearch")
    # es_port = int(os.environ.get("TEST_ELASTICSEARCH_PORT", "9202"))
    # with elasticsearch_test.ElasticsearchTest(port=es_port, es_path=config("TEST_ES_HOME")):
    yield
