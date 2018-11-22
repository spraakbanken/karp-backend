import json

# import pytest


def test_something(client_with_data):
    entries = [{
            "code": 1,
            "name": "test1",
            "population": 3,
            "area": 30000,
            "density": 5,
            "municipality": 1
        }, {
            "code": 2,
            "name": "test2",
            "population": 6,
            "area": 20000,
            "density": 5,
            "municipality": 1
        }, {
            "code": 3,
            "name": "test3",
            "population": 4,
            "area": 50000,
            "density": 5,
            "municipality": 2
        }
    ]
    for entry in entries:
        client_with_data.post('/entry?resource=places',
                              data=json.dumps(entry),
                              content_type='application/json')

    response = client_with_data.get('/entries?resource=places')
    entries = json.loads(response.data.decode())
    assert len(entries) == 3

    names = ['test1', 'test2', 'test3']
    for entry in entries:
        assert entry['name'] in names
        names.remove(entry['name'])
