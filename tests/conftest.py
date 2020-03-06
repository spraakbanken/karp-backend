# pylint: disable=wrong-import-position,missing-function-docstring
"""Pytest entry point."""
from distutils.util import strtobool
import json
import os
import time
from typing import Dict

import pytest  # pyre-ignore

from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

import elasticsearch_test  # pyre-ignore

from karp import create_app  # noqa: E402
from karp.database import db  # noqa: E402
from karp.config import Config  # noqa: E402
import karp.resourcemgr as resourcemgr  # noqa: E402
import karp.indexmgr as indexmgr  # noqa: E402
from karp.database import ResourceDefinition  # noqa: E402


CONFIG_PLACES = """{
  "resource_id": "places",
  "resource_name": "Platser i Sverige",
  "fields": {
    "name": {
      "type": "string",
      "required": true
    },
    "municipality": {
      "collection": true,
      "type": "number",
      "required": true
    },
    "population": {
      "type": "number"
    },
    "area": {
      "type": "number"
    },
    "density": {
      "type": "number"
    },
    "code": {
      "type": "number",
      "required": true
    }
  },
  "sort": "name",
  "id": "code"
}"""


class ConfigTest(Config):
    """[summary]

    Arguments:
        Config {[type]} -- [description]
    """

    SQLALCHEMY_DATABASE_URI = "sqlite://"
    TESTING = True
    SETUP_DATABASE = False
    JWT_AUTH = False
    ELASTICSEARCH_ENABLED = False
    CONSOLE_LOG_LEVEL = "WARNING"

    def __init__(self, use_elasticsearch=False):
        if use_elasticsearch:
            self.ELASTICSEARCH_ENABLED = True
            self.ELASTICSEARCH_HOST = "http://localhost:9201"


@pytest.fixture(name="app_f")
def fixture_app_f():
    """[summary]

    Returns:
        [type] -- [description]

    Yields:
        [type] -- [description]
    """

    def fun(**kwargs):
        app = create_app(ConfigTest(**kwargs))
        with app.app_context():
            ResourceDefinition.__table__.create(bind=db.engine)
            yield app

            db.session.remove()
            db.drop_all()

    return fun


@pytest.fixture(name="app_f_scope_module", scope="module")
def fixture_app_f_scope_module():
    def fun(**kwargs):
        app = create_app(ConfigTest(**kwargs))
        with app.app_context():
            ResourceDefinition.__table__.create(bind=db.engine)
            yield app

            db.session.remove()
            db.drop_all()

    return fun


@pytest.fixture(name="app_f_scope_session", scope="session")
def fixture_app_f_scope_session():
    def fun(**kwargs):
        app = create_app(ConfigTest(**kwargs))
        with app.app_context():
            ResourceDefinition.__table__.create(bind=db.engine)
            yield app

            db.session.remove()
            db.drop_all()

    return fun


@pytest.fixture(name="app_scope_module", scope="module")
def fixture_app_scope_module():
    app = create_app(ConfigTest)
    with app.app_context():
        ResourceDefinition.__table__.create(bind=db.engine)
        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture(name="app_with_data_f")
def fixture_app_with_data_f(app_f):
    def fun(**kwargs):
        app = next(app_f(**kwargs))
        with app.app_context():
            for file in [
                "tests/data/config/places.json",
                "tests/data/config/municipalities.json",
            ]:
                with open(file) as fp:
                    resource, version = resourcemgr.create_new_resource_from_file(fp)
                    resourcemgr.setup_resource_class(resource, version)
                    if kwargs.get("use_elasticsearch", False):
                        indexmgr.publish_index(resource, version)
        return app

    yield fun


@pytest.fixture(name="app_with_data_f_scope_module", scope="module")
def fixture_app_with_data_f_scope_module(app_f_scope_module):
    def fun(**kwargs):
        app = next(app_f_scope_module(**kwargs))
        with app.app_context():
            for file in [
                "tests/data/config/places.json",
                "tests/data/config/municipalities.json",
            ]:
                with open(file) as fp:
                    resource, version = resourcemgr.create_new_resource_from_file(fp)
                    resourcemgr.setup_resource_class(resource, version)
                    if kwargs.get("use_elasticsearch", False):
                        indexmgr.publish_index(resource, version)
        return app

    yield fun


@pytest.fixture(name="app_with_data_f_scope_session", scope="session")
def fixture_app_with_data_f_scope_session(app_f_scope_session):
    def fun(**kwargs):
        app = next(app_f_scope_session(**kwargs))
        with app.app_context():
            for file in [
                "tests/data/config/places.json",
                "tests/data/config/municipalities.json",
            ]:
                with open(file) as fp:
                    resource, version = resourcemgr.create_new_resource(fp)
                    resourcemgr.setup_resource_class(resource, version)
                    if kwargs.get("use_elasticsearch", False):
                        indexmgr.publish_index(resource, version)
        return app

    yield fun


@pytest.fixture(name="app_with_data")
def fixture_app_with_data(app):
    with app.app_context():
        with open("tests/data/config/places.json") as fp:
            resourcemgr.create_new_resource_from_file(fp)
        with open("tests/data/config/municipalities.json") as fp:
            resourcemgr.create_new_resource_from_file(fp)
    return app


@pytest.fixture(name="app_with_data_scope_module", scope="module")
def fixture_app_with_data_scope_module(app_scope_module):
    with app_scope_module.app_context():
        with open("tests/data/config/places.json") as fp:
            resourcemgr.create_new_resource_from_file(fp)
        with open("tests/data/config/municipalities.json") as fp:
            resourcemgr.create_new_resource_from_file(fp)

    return app_scope_module


@pytest.fixture(name="client")
def fixture_client(app_f):
    app = next(app_f())
    return app.test_client()


@pytest.fixture
def client_with_data_f(app_with_data_f):
    def fun(**kwargs):
        app_with_data = app_with_data_f(**kwargs)
        return app_with_data.test_client()

    return fun


@pytest.fixture(scope="module")
def client_with_data_f_scope_module(app_with_data_f_scope_module):
    def fun(**kwargs):
        app_with_data = app_with_data_f_scope_module(**kwargs)
        return app_with_data.test_client()

    return fun


@pytest.fixture(name="client_with_data_f_scope_session", scope="session")
def fixture_client_with_data_f_scope_session(app_with_data_f_scope_session):
    def fun(**kwargs):
        app_with_data = app_with_data_f_scope_session(**kwargs)
        return app_with_data.test_client()

    return fun


@pytest.fixture(name="client_with_data_scope_module", scope="module")
def fixture_client_with_data_scope_module(app_with_data_scope_module):
    return app_with_data_scope_module.test_client()


@pytest.fixture
def runner(app_f):
    app = next(app_f())
    return app.test_cli_runner()


@pytest.fixture(name="es", scope="session")
def fixture_es():
    if not strtobool(os.environ.get("ELASTICSEARCH_ENABLED", "false")):
        pytest.skip("Elasticsearch disabled.")
    else:
        if not os.environ.get("ES_HOME"):
            raise RuntimeError("must set ES_HOME to run tests that use elasticsearch")
        with elasticsearch_test.ElasticsearchTest(port=9201):
            yield "run"


@pytest.fixture
def json_schema_config():
    return json.loads(CONFIG_PLACES)


PLACES = [
    {
        "code": 1,
        "name": "Grund test",
        "population": 3122,
        "area": 6312,
        "density": 6312,
        "municipality": [1],
        "larger_place": 7  # Alhamn
        # "smaller_places": 9 "Bjurvik2"
    },
    {
        "code": 2,
        "name": "Grunds",
        "population": 6312,
        "area": 20000,
        "density": 6,
        "municipality": [1],
    },
    {
        "code": 3,
        "name": "Botten test",
        "population": 4133,
        "area": 50000,
        "density": 7,
        "municipality": [2, 3],
        "larger_place": 8  # "Bjurvik"
        # "smaller_places": 4 "Hambo"
    },
    {
        "code": 4,
        "name": "Hambo",
        "population": 4132,
        "area": 50000,
        "municipality": [2, 3],
        "larger_place": 3  # Botten test
        # "smaller_places": 7 "Alhamn"
    },
    {"code": 5, "name": "Rutvik", "area": 50000, "municipality": [2, 3]},
    {
        "code": 6,
        "name": "Alvik",
        "area": 6312,
        "population": 6312,
        "density": 12,
        "municipality": [3]
        # "smaller_places": 7  "Bjurvik"
    },
    {
        "code": 7,
        "name": "Alhamn",
        "area": 6312,
        "population": 3812,
        "density": 12,
        "municipality": [2, 3],
        "larger_place": 4  # Hambo
        # "smaller_places": 1  "Grund test"
    },
    {
        "code": 8,
        "name": "Bjurvik",
        "area": 6312,
        "population": 6212,
        "density": 12,
        "municipality": [2, 3],
        "larger_place": 6  # Alvik
        # "smaller_places": 1  "Botten test"
    },
    {
        "code": 9,
        "name": "Bjurvik2",
        "area": 7312,
        "population": 641,
        "density": 12,
        "municipality": [2],
        "larger_place": 1,  # Grund test
    },
]


MUNICIPALITIES = [
    {
        "code": 1,
        "name": "Luleå kommun",
        "state": "Norrbottens län",
        "region": "Norrbotten",
        "capital": "Luleå",
        "area": {"land": 2094.08, "water": 148.39},
        "population": {"value": {"total": 77860}, "density": {"total": 37.18}},
    },
    {
        "code": 2,
        "name": "Norsjö kommun",
        "state": "Västerbottens län",
        "region": "Västerbotten",
        "capital": "Norsjö",
        "area": {"land": 1739.15, "water": 184.43},
        "population": {"value": {"total": 4101}, "density": {"total": 2.36}},
    },
    {
        "code": 3,
        "name": "Piteå kommun",
        "state": "Norrbottens län",
        "region": "Norrbotten",
        "capital": "Piteå",
        "area": {"land": 3086.04, "water": 149.04},
        "population": {"value": {"total": 42108}, "density": {"total": 13.64}},
    },
]


def init(client, es_status_code, entries: Dict):
    if es_status_code == "skip":
        pytest.skip("elasticsearch disabled")
    client_with_data = client(use_elasticsearch=True)

    for resource, _entries in entries.items():
        for entry in _entries:
            client_with_data.post(
                "{resource}/add".format(resource=resource),
                data=json.dumps({"entry": entry}),
                content_type="application/json",
            )
    return client_with_data


@pytest.fixture(scope="session")
def client_with_entries_scope_session(es, client_with_data_f_scope_session):
    client_with_data = init(
        client_with_data_f_scope_session,
        es,
        {"places": PLACES, "municipalities": MUNICIPALITIES},
    )
    time.sleep(5)
    return client_with_data
