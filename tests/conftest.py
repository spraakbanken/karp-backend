import pytest  # pyre-ignore
import os
import subprocess
import tempfile
from karp import create_app, db
from karp.config import Config
from karp.models import create_new_resource, publish_resource


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
def es():
    if not os.environ.get('ES_PATH'):
        raise RuntimeError('must set $ES_PATH to run tests that use elasticsearch')
    executable = os.path.join(os.environ.get('ES_PATH') + 'bin/elasticsearch')
    data_arg = '-Epath.data=%s' % tempfile.mkdtemp()
    logs_arg = '-Epath.logs=%s' % tempfile.mkdtemp()
    env_copy = os.environ.copy()
    env_copy['ES_JAVA_OPTS'] = '-Xms512m -Xmx512m'

    p = subprocess.Popen([executable, data_arg, logs_arg], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

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

    yield 'we must yield something?'

    p.kill()
