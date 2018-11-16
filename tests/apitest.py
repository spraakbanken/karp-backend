import unittest
from karp import create_app
from karp.models import create_new_resource, publish_resource

URL = 'http://localhost:5000'


class TestBaseCase(unittest.TestCase):

    def setUp(self) -> None:
        app = create_app({
            'SQLALCHEMY_DATABASE_URI': 'sqlite://'
        })
        self.app = app.test_client()
        with app.app_context():
            create_new_resource('data/config/places.json')
            create_new_resource('data/config/municipalities.json')
            publish_resource('places', 1)
            publish_resource('municipalities', 1)
