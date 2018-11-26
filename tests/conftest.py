import io
import json

import pytest  # pyre-ignore
import os
import subprocess
import tempfile
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


@pytest.fixture
def app_with_data_f(app_f):
    def fun(**kwargs):
        app = next(app_f(**kwargs))
        with app.app_context():
            with open('tests/data/config/places.json') as fp:
                create_new_resource(fp)
            with open('tests/data/config/municipalities.json') as fp:
                create_new_resource(fp)
            publish_resource('places', 1)
            publish_resource('municipalities', 1)

        return app
    return fun


@pytest.fixture(scope="module")
def app_with_data(app_with_config):
    with app.app_context():
        with open('tests/data/places.jsonl') as fp:
            create_new_resource(fp)
        with open('tests/data/municipalities.jsonl') as fp:
            create_new_resource(fp)
        publish_resource('places', 1)
        publish_resource('municipalities', 1)

    return app


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


@pytest.fixture
def runner(app_f):
    app = next(app_f())
    return app.test_cli_runner()


@pytest.fixture
def es():
    if os.environ.get('ELASTICSEARCH_ENABLED') != 'true':
        yield 'skip'
    else:
        if not os.environ.get('ES_PATH'):
            raise RuntimeError('must set $ES_PATH to run tests that use elasticsearch')
        executable = os.path.join(os.environ.get('ES_PATH') + 'bin/elasticsearch')
        data_arg = '-Epath.data=%s' % tempfile.mkdtemp()
        logs_arg = '-Epath.logs=%s' % tempfile.mkdtemp()
        port_arg = '-Ehttp.port=9201'
        env_copy = os.environ.copy()
        env_copy['ES_JAVA_OPTS'] = '-Xms512m -Xmx512m'

        p = subprocess.Popen([executable, data_arg, logs_arg, port_arg], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

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
