import unittest
import json
from karp.app import create_app

URL = 'http://localhost:5000'


class APITest(unittest.TestCase):

    def setUp(self):
        app = create_app({
            'SQLALCHEMY_DATABASE_URI': 'sqlite://'
        })
        self.app = app.test_client()

    def test_something(self):
        self.app.post(URL + '/entry/test1')
        self.app.post(URL + '/entry/test2')
        self.app.post(URL + '/entry/test3')

        entries = json.loads(self.app.get(URL + '/entries').data.decode())
        assert len(entries) == 3

        values = ['test1', 'test2', 'test3']
        for entry in entries:
            assert entry['value'] in values
            values.remove(entry['value'])
