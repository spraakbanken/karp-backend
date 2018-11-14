import json

from apitest import TestBaseCase, URL


class APITest(TestBaseCase):

    def test_something(self):
        entries = [
            {"name": "test1", "population": 3, "area": 30000},
            {"name": "test2", "population": 6, "area": 20000},
            {"name": "test3", "population": 4, "area": 50000}
        ]
        for entry in entries:
            self.app.post(URL + '/entry?resource=places', data=json.dumps(entry), content_type='application/json')

        response = self.app.get(URL + '/entries?resource=places')
        entries = json.loads(response.data.decode())
        assert len(entries) == 3

        names = ['test1', 'test2', 'test3']
        for entry in entries:
            assert entry['name'] in names
            names.remove(entry['name'])
