import io
import json

import pytest  # pyre-ignore
# import os
# import subprocess
# import tempfile
from karp import create_app
from karp.database import db
from karp.config import Config
from karp.resourcemgr import create_new_resource
from karp.resourcemgr import publish_resource


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


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    TESTING = True
    ELASTICSEARCH_URL = 'http://localhost:9200'


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def app_with_data(app):
    with app.app_context():
        with open('tests/data/config/places.json') as fp:
            create_new_resource(fp)
        with open('tests/data/config/municipalities.json') as fp:
            create_new_resource(fp)
        publish_resource('places', 1)
        publish_resource('municipalities', 1)

    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def client_with_data(app_with_data):
    return app_with_data.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def json_schema_config():
    return json.loads(CONFIG_PLACES)
