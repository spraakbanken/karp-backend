import io

import pytest  # pyre-ignore

from karp import create_app, db
from karp.config import Config
from karp.models import create_new_resource, publish_resource


CONFIG_PLACES="""{
  "resource_id": "places",
  "resource_name": "Platser i Sverige",
  "fields": {
    "name": {
      "type": "string",
      "required": true
    },
    "municipality": {
      "collection": true,
      "type": "string",
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
        create_new_resource(io.StringIO(CONFIG_PLACES))
        publish_resource('places', 1)
        # with open('tests/data/config/places.json') as fp:
        #     create_new_resource(fp)
        # with open('tests/data/config/municipalities.json') as fp:
        #     create_new_resource(fp)
        # publish_resource('places', 1)
        # publish_resource('municipalities', 1)

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
