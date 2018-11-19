import unittest
from karp import create_app, db
from karp.models import create_new_resource, publish_resource

URL = 'http://localhost:5000'


class TestConfig:
    SQLALCHEMY_DATABASE_URI = 'sqlite://'


class TestBaseCase(unittest.TestCase):

    def setUp(self):
        app = create_app(TestConfig)
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

        self.app = app.test_client()
        with app.app_context():
            create_new_resource('data/config/places.json')
            create_new_resource('data/config/municipalities.json')
            publish_resource('places', 1)
            publish_resource('municipalities', 1)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

