import unittest
from karp.app import create_app

URL = 'http://localhost:5000'


class TestBaseCase(unittest.TestCase):

    def setUp(self) -> None:
        app = create_app({
            'SQLALCHEMY_DATABASE_URI': 'sqlite://'
        })
        self.app = app.test_client()
