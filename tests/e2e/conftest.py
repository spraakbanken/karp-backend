"""Pytest entry point."""
import elasticsearch_test
from karp.main import AppContext
from karp.resource_commands import ResourceCommands
from karp import auth
from karp.main.config import env
import os
import json
import typing
from typing import Any, Generator, Optional, Tuple

from fastapi import FastAPI
from typer import Typer
from typer.testing import CliRunner

import pytest
from starlette.testclient import TestClient

from tests import common_data, utils
from karp.main import new_session
from dataclasses import replace
from tests.integration.auth.adapters import create_access_token


class AccessToken:
    def __init__(self, access_token):
        self.access_token = access_token

    def as_header(self) -> typing.Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
        }


@pytest.fixture(scope="session")
def apply_migrations():
    from karp.main.migrations import use_cases

    use_cases.run_migrations_up()
    yield


@pytest.fixture(name="app", scope="session")
def fixture_app(
    apply_migrations: None, init_search_service: None
) -> Generator[FastAPI, None, None]:
    from karp.api.main import create_app

    yield create_app()
    print("dropping app")
    app = None  # noqa: F841


@pytest.fixture(name="app_context", scope="function")
def fixture_app_context(app: FastAPI) -> AppContext:
    context = app.state.app_context
    with new_session(context.injector) as injector:
        return replace(context, injector=injector)


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

    with new_session(client.app.state.app_context.injector) as injector:
        resource_commands = injector.get(ResourceCommands)

        resource_commands.create_resource(resource_id, resource_id, resource_config, "")

        resource_commands.publish_resource(
            user="", resource_id=resource_id, version=1, message=""
        )


@pytest.fixture(scope="session", name="fa_data_client")
def fixture_fa_data_client(  # noqa: ANN201
    fa_client,
    admin_token: AccessToken,
):
    create_and_publish_resource(
        fa_client,
        path_to_config="assets/testing/config/municipalities.json",
    )
    create_and_publish_resource(
        fa_client,
        path_to_config="assets/testing/config/places.json",
    )
    utils.add_entries(
        fa_client,
        {"municipalities": common_data.MUNICIPALITIES, "places": common_data.PLACES},
        access_token=admin_token,
    )

    return fa_client


auth_levels: typing.Dict[str, int] = {
    level.value: (idx + 1) * 10 for idx, level in enumerate(auth.PermissionLevel)
}


def create_bearer_token(
    scope: typing.Dict,
    user: Optional[str] = "abc123",
) -> AccessToken:
    levels = auth_levels
    return AccessToken(
        access_token=create_access_token(user, levels, scope),
    )


@pytest.fixture(scope="session")
def user1_token() -> AccessToken:
    return create_bearer_token(
        user="user1",
        scope={
            "lexica": {
                "places": auth_levels[auth.PermissionLevel.write],
            }
        },
    )


@pytest.fixture(scope="session")
def user2_token() -> AccessToken:
    return create_bearer_token(
        user="user2",
        scope={
            "lexica": {
                "places": auth_levels[auth.PermissionLevel.write],
            }
        },
    )


@pytest.fixture(scope="session")
def user4_token() -> AccessToken:
    return create_bearer_token(
        scope={
            "lexica": {
                "places": auth_levels[auth.PermissionLevel.admin],
            }
        },
    )


@pytest.fixture(scope="session")
def admin_token() -> AccessToken:
    return create_bearer_token(
        scope={
            "lexica": {
                "places": auth_levels[auth.PermissionLevel.admin],
                "test_resource": auth_levels[auth.PermissionLevel.admin],
                "municipalities": auth_levels[auth.PermissionLevel.admin],
            }
        },
    )


@pytest.fixture(scope="session")
def read_token() -> AccessToken:
    return create_bearer_token(
        scope={
            "lexica": {
                "places": auth_levels[auth.PermissionLevel.read],
                "test_resource": auth_levels[auth.PermissionLevel.read],
                "municipalities": auth_levels[auth.PermissionLevel.read],
            }
        },
    )


@pytest.fixture(scope="session")
def write_token() -> AccessToken:
    return create_bearer_token(
        scope={
            "lexica": {
                "places": auth_levels[auth.PermissionLevel.write],
                "test_resource": auth_levels[auth.PermissionLevel.write],
                "municipalities": auth_levels[auth.PermissionLevel.write],
            }
        },
    )


@pytest.fixture(scope="session")
def no_municipalities_token() -> AccessToken:
    return create_bearer_token(
        scope={"lexica": {}},
    )


@pytest.fixture(name="init_search_service", scope="session")
def fixture_init_search_service():
    if not env("TEST_ES_HOME"):
        raise RuntimeError("must set ES_HOME to run tests that use elasticsearch")
    es_port = int(os.environ.get("TEST_ELASTICSEARCH_PORT", "9202"))
    with elasticsearch_test.ElasticsearchTest(port=es_port, es_path=env("TEST_ES_HOME")):
        yield
