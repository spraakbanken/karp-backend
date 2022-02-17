"""Pytest entry point."""

# pylint: disable=wrong-import-position,missing-function-docstring
from karp.tests.integration.auth.adapters import create_bearer_token
from karp import auth, config
import os
import json
import typing
from typing import Dict

from fastapi import FastAPI

import alembic
import alembic.config
from karp.foundation.value_objects import make_unique_id
from karp.foundation.commands import CommandBus
import elasticsearch_test  # pyre-ignore

import pytest  # pyre-ignore
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import session, sessionmaker
from starlette.config import environ
from starlette.testclient import TestClient
from tenacity import retry, stop_after_delay

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


@retry(stop=stop_after_delay(10))
def wait_for_main_db_to_come_up(engine):
    return engine.connect()


@pytest.fixture(scope='session')
def setup_environment() -> None:
    os.environ['TESTING'] = '1'
    os.environ['AUTH_JWT_PUBKEY_PATH'] = 'karp/tests/data/pubkey.pem'


@pytest.fixture(scope="session")
def apply_migrations(setup_environment: None):
    config = alembic.config.Config("alembic.ini")

    print("running alembic upgrade ...")
    alembic.command.upgrade(config, 'head')
    yield
    print("running alembic downgrade ...")
    # session.close_all_sessions()
    # alembic.command.downgrade(config, 'base')


@pytest.fixture(name="app", scope='session')
def fixture_app(apply_migrations: None, init_search_service: None):
    from karp.webapp.main import create_app

    app = create_app()
    # app.state.app_context.container.binder.install(TestAuthInfrastructure())
    yield app
    print("dropping app")
    app = None


@pytest.fixture(name='fa_client', scope='session')
def fixture_client(app) -> TestClient:
    with TestClient(app) as client:
        yield client

#     async with LifespanManager(app):
#         async with AsyncClient(
#             app=app,
#             base_url="http://testserver",
#             headers={"Content-Type": "application/json"}
#         ) as client:
#             yield client


def places_published(app):

    with open("karp/tests/data/config/places.json") as fp:
        places_config = json.load(fp)
    resource_id = 'places'

    bus = app.state.app_context.container.get(CommandBus)
    cmd = commands.CreateEntryRepository(
        entity_id=make_unique_id(),
        repository_type='default',
        name=resource_id,
        config=places_config,
        user='local admin',
        message='added',
    )
    try:

        bus.dispatch(cmd)
        bus.dispatch(
            commands.CreateResource(
                resource_id=resource_id,
                name=resource_id,
                entry_repo_id=cmd.entity_id,
                config=places_config,
                user='local admin',
                message='added',
            )
        )
    except errors.IntegrityError:
        raise
    try:
        bus.dispatch(
            commands.PublishResource(
                resource_id=resource_id,
                user=cmd.user,
                message=cmd.message,
            )
        )
    except karp_errors.ResourceAlreadyPublished:
        raise

    return places_config


def municipalities_published(app):

    with open("karp/tests/data/config/municipalities.json") as fp:
        municipalities_config = json.load(fp)

    resource_id = 'municipalities'

    bus = app.state.app_context.container.get(CommandBus)

    try:
        cmd = commands.CreateEntryRepository(
            entity_id=make_unique_id(),
            repository_type='default',
            name=resource_id,
            config=municipalities_config,
            user='local admin',
            message='added',
        )
        bus.dispatch(cmd)
        cmd = commands.CreateResource.from_dict(
            municipalities_config,
            entry_repo_id=cmd.entity_id,
            user=cmd.user,
        )
        bus.dispatch(cmd)
    except errors.IntegrityError:
        raise
    try:
        bus.dispatch(
            commands.PublishResource(
                resource_id=cmd.resource_id,
                user=cmd.user,
                message=cmd.message,
            )
        )
    except karp_errors.ResourceAlreadyPublished:
        raise

    return municipalities_config


@pytest.fixture(scope="session", name="fa_data_client")
# @pytest.mark.usefixtures("places_published")
# @pytest.mark.usefixtures("main_db")
def fixture_fa_data_client(
    fa_client,
    admin_token: auth.AccessToken,
):
    places_published(fa_client.app)
    municipalities_published(fa_client.app)
    # utils.add_entries(
    #     fa_client,
    #     {"places": common_data.PLACES, "municipalities": common_data.MUNICIPALITIES},
    #     access_token=admin_token,
    # )

    return fa_client


@pytest.fixture(scope='session')
def auth_levels() -> typing.Dict[str, int]:
    curr_level = 10
    levels = {}
    for level in auth.PermissionLevel:
        levels[level.name] = curr_level
        curr_level += 10

    return levels


@pytest.fixture(scope='session')
def user1_token(auth_levels: typing.Dict[str, int]) -> auth.AccessToken:
    return create_bearer_token(
        user='user1',
        levels=auth_levels,
        scope={
            'lexica': {
                'places': auth_levels[auth.PermissionLevel.write],
            }
        }
    )


@pytest.fixture(scope='session')
def user2_token(auth_levels: typing.Dict[str, int]) -> auth.AccessToken:
    return create_bearer_token(
        user='user2',
        levels=auth_levels,
        scope={
            'lexica': {
                'places': auth_levels[auth.PermissionLevel.write],
            }
        }
    )


@pytest.fixture(scope='session')
def user4_token(auth_levels: typing.Dict[str, int]) -> auth.AccessToken:
    return create_bearer_token(
        user='user4',
        levels=auth_levels,
        scope={
            'lexica': {
                'places': auth_levels[auth.PermissionLevel.admin],
            }
        }
    )


@pytest.fixture(scope='session')
def admin_token(auth_levels: typing.Dict[str, int]) -> auth.AccessToken:
    return create_bearer_token(
        user='alice@example.com',
        levels=auth_levels,
        scope={
            'lexica': {
                'places': auth_levels[auth.PermissionLevel.admin],
                'test_resource': auth_levels[auth.PermissionLevel.admin],
                'municipalities': auth_levels[auth.PermissionLevel.admin],
            }
        }
    )


@pytest.fixture(scope='session')
def read_token(auth_levels: typing.Dict[str, int]) -> auth.AccessToken:
    return create_bearer_token(
        user='alice@example.com',
        levels=auth_levels,
        scope={
            'lexica': {
                'places': auth_levels[auth.PermissionLevel.read],
                'test_resource': auth_levels[auth.PermissionLevel.read],
                'municipalities': auth_levels[auth.PermissionLevel.read],
            }
        }
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
            raise RuntimeError(
                "must set ES_HOME to run tests that use elasticsearch")
        with elasticsearch_test.ElasticsearchTest(
            port=9202, es_path=config.TEST_ES_HOME
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
