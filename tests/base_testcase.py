import unittest
from karp.app import create_app

URL = 'http://localhost:5000'


class APITestBaseCase(unittest.TestCase):

    def setUp(self):
        app = create_app({
            'SQLALCHEMY_DATABASE_URI': 'sqlite://'
        })
        self.app = app.test_client()
