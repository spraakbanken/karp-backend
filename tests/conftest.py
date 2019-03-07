import json

import pytest  # pyre-ignore
import os
from distutils.util import strtobool
import elasticsearch_test

from karp import create_app
from karp.database import db
from karp.config import Config
import karp.resourcemgr as resourcemgr
import karp.indexmgr as indexmgr
from karp.database import ResourceDefinition


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
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    TESTING = True
    SETUP_DATABASE = False
    JWT_AUTH = False
    ELASTICSEARCH_ENABLED = False
    CONSOLE_LOG_LEVEL = 'WARNING'

    def __init__(self, use_elasticsearch=False):
        if use_elasticsearch:
            self.ELASTICSEARCH_ENABLED = True
            self.ELASTICSEARCH_HOST = 'http://localhost:9201'


@pytest.fixture
def app_f():
    def fun(**kwargs):
        app = create_app(ConfigTest(**kwargs))
        with app.app_context():
            ResourceDefinition.__table__.create(bind=db.engine)
            yield app

            db.session.remove()
            db.drop_all()
    return fun


@pytest.fixture(scope="module")
def app_scope_module():
    app = create_app(ConfigTest)
    with app.app_context():
        ResourceDefinition.__table__.create(bind=db.engine)
        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def app_with_data_f(app_f):
    def fun(**kwargs):
        app = next(app_f(**kwargs))
        with app.app_context():
            for file in ['tests/data/config/places.json', 'tests/data/config/municipalities.json']:
                with open(file) as fp:
                    resource, version = resourcemgr.create_new_resource(fp)
                    resourcemgr.setup_resource_class(resource, version)
                    if kwargs.get('use_elasticsearch', False):
                        indexmgr.publish_index(resource, version)
        return app
    yield fun


@pytest.fixture
def app_with_data(app):
    with app.app_context():
        with open('tests/data/config/places.json') as fp:
            resourcemgr.create_new_resource(fp)
        with open('tests/data/config/municipalities.json') as fp:
            resourcemgr.create_new_resource(fp)

    return app


@pytest.fixture(scope="module")
def app_with_data_scope_module(app_scope_module):
    with app_scope_module.app_context():
        with open('tests/data/config/places.json') as fp:
            resourcemgr.create_new_resource(fp)
        with open('tests/data/config/municipalities.json') as fp:
            resourcemgr.create_new_resource(fp)

    return app_scope_module


@pytest.fixture
def client(app_f):
    app = next(app_f())
    return app.test_client()


@pytest.fixture
def client_with_data_f(app_with_data_f):

    def fun(**kwargs):
        app_with_data = app_with_data_f(**kwargs)
        return app_with_data.test_client()

    return fun


@pytest.fixture(scope="module")
def client_with_data_scope_module(app_with_data_scope_module):
    return app_with_data_scope_module.test_client()


@pytest.fixture
def runner(app_f):
    app = next(app_f())
    return app.test_cli_runner()


@pytest.fixture(scope="session")
def es():
    if not strtobool(os.environ.get('ELASTICSEARCH_ENABLED', 'false')):
        yield 'skip'
    else:
        if not os.environ.get('ES_HOME'):
            raise RuntimeError('must set $ES_HOME to run tests that use elasticsearch')
        with elasticsearch_test.ElasticsearchTest(port=9201):
            yield 'run'


@pytest.fixture
def json_schema_config():
    return json.loads(CONFIG_PLACES)
