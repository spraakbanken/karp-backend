"""Pytest entry point."""

# pylint: disable=wrong-import-position,missing-function-docstring

import json
import os
import time
from typing import Dict

import pytest  # pyre-ignore

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from alembic.config import main as alembic_main

from starlette.testclient import TestClient
from starlette.config import environ

environ["TESTING"] = "True"
environ["ELASTICSEARCH_HOST"] = "localhost:9202"

import elasticsearch_test  # pyre-ignore

# from karp.domain.models.resource import create_resource

# # from karp.infrastructure.unit_of_work import unit_of_work
# from karp.infrastructure.sql import sql_entry_repository
# from karp.infrastructure.testing import dummy_auth_service

# # from karp.application import ctx, config
# # from karp.application.services import contexts, entries, resources

# from karp.webapp import main as webapp_main

# from karp.tests import common_data


from karp.infrastructure.sql.db import metadata


@pytest.fixture(name="in_memory_sqlite_db")
def fixture_in_memory_sqlite_db():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return engine


@pytest.fixture
def sqlite_session_factory(in_memory_sqlite_db):
    yield sessionmaker(bind=in_memory_sqlite_db)


# @pytest.fixture(name="db_setup")
# def fixture_db_setup():
#     print("running alembic upgrade ...")
#     alembic_main(["--raiseerr", "upgrade", "head"])
#     yield
#     print("running alembic downgrade ...")
#     alembic_main(["--raiseerr", "downgrade", "base"])


# @pytest.fixture(name="db_setup_scope_module", scope="module")
# def fixture_db_setup_scope_module():
#     print("running alembic upgrade ...")
#     alembic_main(["--raiseerr", "upgrade", "head"])
#     yield
#     print("running alembic downgrade ...")
#     alembic_main(["--raiseerr", "downgrade", "base"])


# @pytest.fixture(name="db_setup_scope_session", scope="session")
# def fixture_db_setup_scope_session():
#     print("running alembic upgrade ...")
#     alembic_main(["--raiseerr", "upgrade", "head"])
#     yield
#     print("running alembic downgrade ...")
#     alembic_main(["--raiseerr", "downgrade", "base"])


# @pytest.fixture(name="fa_client")
# def fixture_fa_client(db_setup, es):
#     ctx.auth_service = dummy_auth_service.DummyAuthService()
#     with TestClient(webapp_main.create_app()) as client:
#         yield client


# @pytest.fixture(name="fa_client_wo_db")
# def fixture_fa_client_wo_db():
#     ctx.auth_service = dummy_auth_service.DummyAuthService()
#     with TestClient(webapp_main.create_app(with_context=False)) as client:
#         yield client


# @pytest.fixture(name="fa_client_scope_module", scope="module")
# def fixture_fa_client_scope_module(db_setup_scope_module):
#     ctx.auth_service = dummy_auth_service.DummyAuthService()
#     with TestClient(webapp_main.create_app()) as client:
#         yield client
#         print("releasing testclient")


# @pytest.fixture(name="fa_client_scope_session", scope="session")
# def fixture_fa_client_scope_session(db_setup_scope_session):
#     ctx.auth_service = dummy_auth_service.DummyAuthService()
#     with TestClient(webapp_main.create_app()) as client:
#         yield client
#         print("releasing testclient")


# @pytest.fixture(name="places")
# def fixture_places():
#     with open("karp/tests/data/config/places.json") as fp:
#         places_config = json.load(fp)

#     resource = create_resource(places_config)

#     yield resource

#     # if resource._entry_repository:
#     resource.entry_repository.teardown()


# @pytest.fixture(name="places_scope_module", scope="module")
# def fixture_places_scope_module(context_scope_module):
#     with open("karp/tests/data/config/places.json") as fp:
#         resource = resources.create_new_resource_from_file(fp)

#     yield resource
#     print("cleaning up places")
#     resource.entry_repository.teardown()


# @pytest.fixture(name="municipalities_scope_module", scope="module")
# def fixture_municipalities_scope_module(context_scope_module):
#     with open("karp/tests/data/config/municipalities.json") as fp:
#         resource = resources.create_new_resource_from_file(fp)

#     yield resource
#     print("cleaning up municipalities")
#     resource.entry_repository.teardown()


# @pytest.fixture(name="context")
# def fixture_context(db_setup, es):
#     contexts.init_context()


# @pytest.fixture(name="context_scope_module", scope="module")
# def fixture_context_scope_module(db_setup_scope_module, es):
#     contexts.init_context()


# @pytest.fixture(name="context_scope_session", scope="session")
# def fixture_context_scope_session(db_setup_scope_session, es):
#     contexts.init_context()


# @pytest.fixture(name="places_published")
# def fixture_places_published(places, db_setup):
#     places.is_published = True
#     with unit_of_work(using=ctx.resource_repo) as uw:
#         uw.put(places)

#     return places


# @pytest.fixture(name="places_published_scope_module", scope="module")
# def fixture_places_published_scope_module(places_scope_module):
#     resources.publish_resource(places_scope_module.resource_id)

#     return places_scope_module


# @pytest.fixture(name="municipalities_published_scope_module", scope="module")
# def fixture_municipalities_published_scope_module(municipalities_scope_module):
#     resources.publish_resource(municipalities_scope_module.resource_id)

#     return municipalities_scope_module


# @pytest.fixture(name="fa_client_w_places")
# def fixture_fa_client_w_places(fa_client, places_published, es):

#     return fa_client


# @pytest.fixture(name="fa_client_w_places_scope_module", scope="module")
# def fixture_fa_client_w_places_scope_module(
#     fa_client_scope_module, places_published_scope_module, es
# ):

#     return fa_client_scope_module


# @pytest.fixture(name="fa_client_w_places_w_municipalities_scope_module", scope="module")
# def fixture_fa_client_w_places_w_municipalities_scope_module(
#     fa_client_scope_module,
#     places_published_scope_module,
#     municipalities_published_scope_module,
#     es,
# ):

#     return fa_client_scope_module


# # from dotenv import load_dotenv
# #
# # load_dotenv(dotenv_path=".env")
# #
# #
# # from karp.infrastructure.sql.sql_models import db
# # from karp import create_app  # noqa: E402
# # from karp.config import Config  # noqa: E402
# # import karp.resourcemgr as resourcemgr  # noqa: E402
# # import karp.indexmgr as indexmgr  # noqa: E402
# # from karp.database import ResourceDefinition  # noqa: E402
# #
# #

# #
# #
# # class ConfigTest(Config):
# #     """[summary]
# #
# #     Arguments:
# #         Config {[type]} -- [description]
# #     """
# #
# #     SQLALCHEMY_DATABASE_URI = "sqlite://"
# #     TESTING = True
# #     SETUP_DATABASE = False
# #     JWT_AUTH = False
# #     ELASTICSEARCH_ENABLED = False
# #     CONSOLE_LOG_LEVEL = "WARNING"
# #
# #     def __init__(self, use_elasticsearch=False):
# #         if use_elasticsearch:
# #             self.ELASTICSEARCH_ENABLED = True
# #             self.ELASTICSEARCH_HOST = "http://localhost:9201"
# #
# #
# # @pytest.fixture(name="app_f")
# # def fixture_app_f():
# #     """[summary]
# #
# #     Returns:
# #         [type] -- [description]
# #
# #     Yields:
# #         [type] -- [description]
# #     """
# #
# #     def fun(**kwargs):
# #         app = create_app(ConfigTest(**kwargs))
# #         with app.app_context():
# #             ResourceDefinition.__table__.create(bind=db.engine)
# #             yield app
# #
# #             db.session.remove()
# #             db.drop_all()
# #
# #     return fun
# #
# #
# # @pytest.fixture(name="app_f_scope_module", scope="module")
# # def fixture_app_f_scope_module():
# #     def fun(**kwargs):
# #         app = create_app(ConfigTest(**kwargs))
# #         with app.app_context():
# #             ResourceDefinition.__table__.create(bind=db.engine)
# #             yield app
# #
# #             db.session.remove()
# #             db.drop_all()
# #
# #     return fun
# #
# #
# # @pytest.fixture(name="app_f_scope_session", scope="session")
# # def fixture_app_f_scope_session():
# #     def fun(**kwargs):
# #         app = create_app(ConfigTest(**kwargs))
# #         with app.app_context():
# #             ResourceDefinition.__table__.create(bind=db.engine)
# #             yield app
# #
# #             db.session.remove()
# #             db.drop_all()
# #
# #     return fun
# #
# #
# # @pytest.fixture(name="app_scope_module", scope="module")
# # def fixture_app_scope_module():
# #     app = create_app(ConfigTest)
# #     with app.app_context():
# #         ResourceDefinition.__table__.create(bind=db.engine)
# #         yield app
# #
# #         db.session.remove()
# #         db.drop_all()
# #
# #
# # @pytest.fixture(name="app_with_data_f")
# # def fixture_app_with_data_f(app_f):
# #     def fun(**kwargs):
# #         app = next(app_f(**kwargs))
# #         with app.app_context():
# #             for file in [
# #                 "karp/tests/data/config/places.json",
# #                 "karp/tests/data/config/municipalities.json",
# #             ]:
# #                 with open(file) as fp:
# #                     resource, version = resourcemgr.create_new_resource_from_file(fp)
# #                     resourcemgr.setup_resource_class(resource, version)
# #                     if kwargs.get("use_elasticsearch", False):
# #                         indexmgr.publish_index(resource, version)
# #         return app
# #
# #     yield fun
# #
# #
# # @pytest.fixture(name="app_with_data_f_scope_module", scope="module")
# # def fixture_app_with_data_f_scope_module(app_f_scope_module):
# #     def fun(**kwargs):
# #         app = next(app_f_scope_module(**kwargs))
# #         with app.app_context():
# #             for file in [
# #                 "karp/tests/data/config/places.json",
# #                 "karp/tests/data/config/municipalities.json",
# #             ]:
# #                 with open(file) as fp:
# #                     resource, version = resourcemgr.create_new_resource_from_file(fp)
# #                     resourcemgr.setup_resource_class(resource, version)
# #                     if kwargs.get("use_elasticsearch", False):
# #                         indexmgr.publish_index(resource, version)
# #         return app
# #
# #     yield fun
# #
# #
# # @pytest.fixture(name="app_with_data_f_scope_session", scope="session")
# # def fixture_app_with_data_f_scope_session(app_f_scope_session):
# #     def fun(**kwargs):
# #         app = next(app_f_scope_session(**kwargs))
# #         with app.app_context():
# #             for file in [
# #                 "karp/tests/data/config/places.json",
# #                 "karp/tests/data/config/municipalities.json",
# #             ]:
# #                 with open(file) as fp:
# #                     resource, version = resourcemgr.create_new_resource(fp)
# #                     resourcemgr.setup_resource_class(resource, version)
# #                     if kwargs.get("use_elasticsearch", False):
# #                         indexmgr.publish_index(resource, version)
# #         return app
# #
# #     yield fun
# #
# #
# # @pytest.fixture(name="app_with_data")
# # def fixture_app_with_data(app):
# #     with app.app_context():
# #         with open("karp/tests/data/config/places.json") as fp:
# #             resourcemgr.create_new_resource_from_file(fp)
# #         with open("karp/tests/data/config/municipalities.json") as fp:
# #             resourcemgr.create_new_resource_from_file(fp)
# #     return app
# #
# #
# # @pytest.fixture(name="app_with_data_scope_module", scope="module")
# # def fixture_app_with_data_scope_module(app_scope_module):
# #     with app_scope_module.app_context():
# #         with open("karp/tests/data/config/places.json") as fp:
# #             resourcemgr.create_new_resource_from_file(fp)
# #         with open("karp/tests/data/config/municipalities.json") as fp:
# #             resourcemgr.create_new_resource_from_file(fp)
# #
# #     return app_scope_module
# #
# #
# # @pytest.fixture(name="client")
# # def fixture_client(app_f):
# #     app = next(app_f())
# #     return app.test_client()
# #
# #
# # @pytest.fixture
# # def client_with_data_f(app_with_data_f):
# #     def fun(**kwargs):
# #         app_with_data = app_with_data_f(**kwargs)
# #         return app_with_data.test_client()
# #
# #     return fun
# #
# #
# # @pytest.fixture(scope="module")
# # def client_with_data_f_scope_module(app_with_data_f_scope_module):
# #     def fun(**kwargs):
# #         app_with_data = app_with_data_f_scope_module(**kwargs)
# #         return app_with_data.test_client()
# #
# #     return fun
# #
# #
# # @pytest.fixture(name="client_with_data_f_scope_session", scope="session")
# # def fixture_client_with_data_f_scope_session(app_with_data_f_scope_session):
# #     def fun(**kwargs):
# #         app_with_data = app_with_data_f_scope_session(**kwargs)
# #         return app_with_data.test_client()
# #
# #     return fun
# #
# #
# # @pytest.fixture(name="client_with_data_scope_module", scope="module")
# # def fixture_client_with_data_scope_module(app_with_data_scope_module):
# #     return app_with_data_scope_module.test_client()
# #
# #
# # @pytest.fixture
# # def runner(app_f):
# #     app = next(app_f())
# #     return app.test_cli_runner()
# #
# #
# @pytest.fixture(name="es", scope="session")
# def fixture_es():
#     if not config.TEST_ELASTICSEARCH_ENABLED:
#         yield "no_es"
#     else:
#         if not config.TEST_ES_HOME:
#             raise RuntimeError("must set ES_HOME to run tests that use elasticsearch")
#         with elasticsearch_test.ElasticsearchTest(
#             port=9202, es_path=config.TEST_ES_HOME
#         ):
#             yield "run"


# @pytest.fixture
# def json_schema_config():
#     return common_data.CONFIG_PLACES


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
