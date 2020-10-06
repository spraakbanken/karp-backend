# pylint: disable=wrong-import-position,missing-function-docstring
"""Pytest entry point."""
from distutils.util import strtobool
import json
import os
import time
from typing import Dict

import pytest  # pyre-ignore

from alembic.config import main as alembic_main

from starlette.testclient import TestClient
from starlette.config import environ

environ["TESTING"] = "True"
environ["ELASTICSEARCH_HOST"] = "localhost:9201"

import elasticsearch_test  # pyre-ignore

from karp.domain.models.resource import create_resource

from karp.infrastructure.unit_of_work import unit_of_work
from karp.infrastructure.sql import sql_entry_repository
from karp.infrastructure.testing import dummy_auth_service

from karp.application import ctx, config

from karp.webapp import main as webapp_main

from tests import common_data


@pytest.fixture(name="db_setup")
def fixture_db_setup():
    alembic_main(["--raiseerr", "upgrade", "head"])
    yield
    alembic_main(["--raiseerr", "downgrade", "base"])


@pytest.fixture(name="db_setup_scope_module", scope="module")
def fixture_db_setup_scope_module():
    print("running alembic upgrade ...")
    alembic_main(["--raiseerr", "upgrade", "head"])
    yield
    print("running alembic downgrade ...")
    alembic_main(["--raiseerr", "downgrade", "base"])


@pytest.fixture(name="fa_client")
def fixture_fa_client(db_setup, es):
    assert es == "run"
    ctx.auth_service = dummy_auth_service.DummyAuthService()
    with TestClient(webapp_main.create_app()) as client:
        yield client


@pytest.fixture(name="fa_client_scope_module", scope="module")
def fixture_fa_client_scope_module(db_setup_scope_module):
    ctx.auth_service = dummy_auth_service.DummyAuthService()
    with TestClient(webapp_main.create_app()) as client:
        yield client
        print("releasing testclient")


@pytest.fixture(name="places")
def fixture_places():
    with open("tests/data/config/places.json") as fp:
        places_config = json.load(fp)

    resource = create_resource(places_config)

    yield resource

    # if resource._entry_repository:
    resource.entry_repository.teardown()


@pytest.fixture(name="places_scope_module", scope="module")
def fixture_places_scope_module():
    with open("tests/data/config/places.json") as fp:
        places_config = json.load(fp)

    resource = create_resource(places_config)

    yield resource
    print("cleaning up places")
    # if resource._entry_repository:
    resource.entry_repository.teardown()


@pytest.fixture(name="fa_client_w_places")
def fixture_fa_client_w_places(fa_client, places, es):
    assert es == "run"
    places.is_published = True
    with unit_of_work(using=ctx.resource_repo) as uw:
        uw.put(places)

    return fa_client


@pytest.fixture(name="fa_client_w_places_scope_module", scope="module")
def fixture_fa_client_w_places_scope_module(
    fa_client_scope_module, places_scope_module
):
    places_scope_module.is_published = True
    with unit_of_work(using=ctx.resource_repo) as uw:
        uw.put(places_scope_module)

    return fa_client_scope_module


# from dotenv import load_dotenv
#
# load_dotenv(dotenv_path=".env")
#
#
# from karp.infrastructure.sql.sql_models import db
# from karp import create_app  # noqa: E402
# from karp.config import Config  # noqa: E402
# import karp.resourcemgr as resourcemgr  # noqa: E402
# import karp.indexmgr as indexmgr  # noqa: E402
# from karp.database import ResourceDefinition  # noqa: E402
#
#
# CONFIG_PLACES = """{
#   "resource_id": "places",
#   "resource_name": "Platser i Sverige",
#   "fields": {
#     "name": {
#       "type": "string",
#       "required": true
#     },
#     "municipality": {
#       "collection": true,
#       "type": "number",
#       "required": true
#     },
#     "population": {
#       "type": "number"
#     },
#     "area": {
#       "type": "number"
#     },
#     "density": {
#       "type": "number"
#     },
#     "code": {
#       "type": "number",
#       "required": true
#     }
#   },
#   "sort": "name",
#   "id": "code"
# }"""
#
#
# class ConfigTest(Config):
#     """[summary]
#
#     Arguments:
#         Config {[type]} -- [description]
#     """
#
#     SQLALCHEMY_DATABASE_URI = "sqlite://"
#     TESTING = True
#     SETUP_DATABASE = False
#     JWT_AUTH = False
#     ELASTICSEARCH_ENABLED = False
#     CONSOLE_LOG_LEVEL = "WARNING"
#
#     def __init__(self, use_elasticsearch=False):
#         if use_elasticsearch:
#             self.ELASTICSEARCH_ENABLED = True
#             self.ELASTICSEARCH_HOST = "http://localhost:9201"
#
#
# @pytest.fixture(name="app_f")
# def fixture_app_f():
#     """[summary]
#
#     Returns:
#         [type] -- [description]
#
#     Yields:
#         [type] -- [description]
#     """
#
#     def fun(**kwargs):
#         app = create_app(ConfigTest(**kwargs))
#         with app.app_context():
#             ResourceDefinition.__table__.create(bind=db.engine)
#             yield app
#
#             db.session.remove()
#             db.drop_all()
#
#     return fun
#
#
# @pytest.fixture(name="app_f_scope_module", scope="module")
# def fixture_app_f_scope_module():
#     def fun(**kwargs):
#         app = create_app(ConfigTest(**kwargs))
#         with app.app_context():
#             ResourceDefinition.__table__.create(bind=db.engine)
#             yield app
#
#             db.session.remove()
#             db.drop_all()
#
#     return fun
#
#
# @pytest.fixture(name="app_f_scope_session", scope="session")
# def fixture_app_f_scope_session():
#     def fun(**kwargs):
#         app = create_app(ConfigTest(**kwargs))
#         with app.app_context():
#             ResourceDefinition.__table__.create(bind=db.engine)
#             yield app
#
#             db.session.remove()
#             db.drop_all()
#
#     return fun
#
#
# @pytest.fixture(name="app_scope_module", scope="module")
# def fixture_app_scope_module():
#     app = create_app(ConfigTest)
#     with app.app_context():
#         ResourceDefinition.__table__.create(bind=db.engine)
#         yield app
#
#         db.session.remove()
#         db.drop_all()
#
#
# @pytest.fixture(name="app_with_data_f")
# def fixture_app_with_data_f(app_f):
#     def fun(**kwargs):
#         app = next(app_f(**kwargs))
#         with app.app_context():
#             for file in [
#                 "tests/data/config/places.json",
#                 "tests/data/config/municipalities.json",
#             ]:
#                 with open(file) as fp:
#                     resource, version = resourcemgr.create_new_resource_from_file(fp)
#                     resourcemgr.setup_resource_class(resource, version)
#                     if kwargs.get("use_elasticsearch", False):
#                         indexmgr.publish_index(resource, version)
#         return app
#
#     yield fun
#
#
# @pytest.fixture(name="app_with_data_f_scope_module", scope="module")
# def fixture_app_with_data_f_scope_module(app_f_scope_module):
#     def fun(**kwargs):
#         app = next(app_f_scope_module(**kwargs))
#         with app.app_context():
#             for file in [
#                 "tests/data/config/places.json",
#                 "tests/data/config/municipalities.json",
#             ]:
#                 with open(file) as fp:
#                     resource, version = resourcemgr.create_new_resource_from_file(fp)
#                     resourcemgr.setup_resource_class(resource, version)
#                     if kwargs.get("use_elasticsearch", False):
#                         indexmgr.publish_index(resource, version)
#         return app
#
#     yield fun
#
#
# @pytest.fixture(name="app_with_data_f_scope_session", scope="session")
# def fixture_app_with_data_f_scope_session(app_f_scope_session):
#     def fun(**kwargs):
#         app = next(app_f_scope_session(**kwargs))
#         with app.app_context():
#             for file in [
#                 "tests/data/config/places.json",
#                 "tests/data/config/municipalities.json",
#             ]:
#                 with open(file) as fp:
#                     resource, version = resourcemgr.create_new_resource(fp)
#                     resourcemgr.setup_resource_class(resource, version)
#                     if kwargs.get("use_elasticsearch", False):
#                         indexmgr.publish_index(resource, version)
#         return app
#
#     yield fun
#
#
# @pytest.fixture(name="app_with_data")
# def fixture_app_with_data(app):
#     with app.app_context():
#         with open("tests/data/config/places.json") as fp:
#             resourcemgr.create_new_resource_from_file(fp)
#         with open("tests/data/config/municipalities.json") as fp:
#             resourcemgr.create_new_resource_from_file(fp)
#     return app
#
#
# @pytest.fixture(name="app_with_data_scope_module", scope="module")
# def fixture_app_with_data_scope_module(app_scope_module):
#     with app_scope_module.app_context():
#         with open("tests/data/config/places.json") as fp:
#             resourcemgr.create_new_resource_from_file(fp)
#         with open("tests/data/config/municipalities.json") as fp:
#             resourcemgr.create_new_resource_from_file(fp)
#
#     return app_scope_module
#
#
# @pytest.fixture(name="client")
# def fixture_client(app_f):
#     app = next(app_f())
#     return app.test_client()
#
#
# @pytest.fixture
# def client_with_data_f(app_with_data_f):
#     def fun(**kwargs):
#         app_with_data = app_with_data_f(**kwargs)
#         return app_with_data.test_client()
#
#     return fun
#
#
# @pytest.fixture(scope="module")
# def client_with_data_f_scope_module(app_with_data_f_scope_module):
#     def fun(**kwargs):
#         app_with_data = app_with_data_f_scope_module(**kwargs)
#         return app_with_data.test_client()
#
#     return fun
#
#
# @pytest.fixture(name="client_with_data_f_scope_session", scope="session")
# def fixture_client_with_data_f_scope_session(app_with_data_f_scope_session):
#     def fun(**kwargs):
#         app_with_data = app_with_data_f_scope_session(**kwargs)
#         return app_with_data.test_client()
#
#     return fun
#
#
# @pytest.fixture(name="client_with_data_scope_module", scope="module")
# def fixture_client_with_data_scope_module(app_with_data_scope_module):
#     return app_with_data_scope_module.test_client()
#
#
# @pytest.fixture
# def runner(app_f):
#     app = next(app_f())
#     return app.test_cli_runner()
#
#
@pytest.fixture(name="es", scope="session")
def fixture_es():
    if not config.TEST_ELASTICSEARCH_ENABLED:
        yield "no_es"
    else:
        if not config.TEST_ES_HOME:
            raise RuntimeError("must set ES_HOME to run tests that use elasticsearch")
        with elasticsearch_test.ElasticsearchTest(
            port=9201, es_path=config.TEST_ES_HOME
        ):
            yield "run"


@pytest.fixture
def json_schema_config():
    return json.loads(common_data.CONFIG_PLACES)


# def init(client, es_status_code, entries: Dict):
#     if es_status_code == "skip":
#         pytest.skip("elasticsearch disabled")
#     client_with_data = client(use_elasticsearch=True)
#
#     for resource, _entries in entries.items():
#         for entry in _entries:
#             client_with_data.post(
#                 "{resource}/add".format(resource=resource),
#                 data=json.dumps({"entry": entry}),
#                 content_type="application/json",
#             )
#     return client_with_data
#
#
# @pytest.fixture(scope="session")
# def client_with_entries_scope_session(es, client_with_data_f_scope_session):
#     client_with_data = init(
#         client_with_data_f_scope_session,
#         es,
#         {"places": PLACES, "municipalities": MUNICIPALITIES},
#     )
#     time.sleep(5)
#     return client_with_data
