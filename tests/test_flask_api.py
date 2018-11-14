import json

from apitest import TestBaseCase, URL


class APITest(TestBaseCase):

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
