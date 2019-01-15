import json

import pytest  # pyre-ignore
import os
import subprocess
import tempfile
from distutils.util import strtobool

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


class ConfigTest(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    TESTING = True

    def __init__(self, use_elasticsearch=False):
        if use_elasticsearch:
            self.ELASTICSEARCH_HOST = 'http://localhost:9201'


@pytest.fixture
def app_f():
    def fun(**kwargs):
        app = create_app(ConfigTest(**kwargs))
        with app.app_context():
            yield app

            db.session.remove()
            db.drop_all()
    return fun


@pytest.fixture(scope="module")
def app_scope_module():
    app = create_app(ConfigTest)
    with app.app_context():
        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def app_with_data_f(app_f):
    def fun(**kwargs):
        app = next(app_f(**kwargs))
        with app.app_context():
            with open('tests/data/config/places.json') as fp:
                resource, version = create_new_resource(fp)
                publish_resource(resource, version)
            with open('tests/data/config/municipalities.json') as fp:
                resource, version = create_new_resource(fp)
                publish_resource(resource, version)
            # publish_resource('places', 1)
            # publish_resource('municipalities', 1)

        return app
    yield fun


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


@pytest.fixture(scope="module")
def app_with_data_scope_module(app_scope_module):
    with app_scope_module.app_context():
        with open('tests/data/config/places.json') as fp:
            create_new_resource(fp)
        with open('tests/data/config/municipalities.json') as fp:
            create_new_resource(fp)
        publish_resource('places', 1)
        publish_resource('municipalities', 1)

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
        if not os.environ.get('ES_PATH'):
            raise RuntimeError('must set $ES_PATH to run tests that use elasticsearch')
        executable = os.path.join(os.environ.get('ES_PATH') + 'bin/elasticsearch')
        data_arg = '-Epath.data=%s' % tempfile.mkdtemp()
        logs_arg = '-Epath.logs=%s' % tempfile.mkdtemp()
        port_arg = '-Ehttp.port=9201'
        cluster_arg = '-Ecluster.name=testcluster'
        env_copy = os.environ.copy()
        env_copy['ES_JAVA_OPTS'] = '-Xms512m -Xmx512m'

        p = subprocess.Popen([executable, data_arg, logs_arg, port_arg, cluster_arg],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             env=env_copy)

        line = ''
        while True:
            out = p.stdout.read(1)
            if out == b'' and p.poll() is not None:
                raise RuntimeError('Failed to start Elasticsearch')
            if out:
                char = out.decode()
                if char != '\n':
                    line += char
                else:
                    line = ''

            if 'started' in line:
                break

        yield 'run'

        p.kill()


@pytest.fixture
def json_schema_config():
    return json.loads(CONFIG_PLACES)
