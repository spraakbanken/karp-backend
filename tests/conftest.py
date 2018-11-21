import pytest

from karp import create_app, db
from karp.config import BaseConfig
from karp.models import create_new_resource, publish_resource


class TestConfig(BaseConfig):
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
