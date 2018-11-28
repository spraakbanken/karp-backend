import json
import time
import urllib.request
import urllib.parse
from karp import search


def test_es_setup(es):
    url = 'http://localhost:' + str(es)
    f = urllib.request.urlopen(url)
    answer = json.loads(f.read().decode('utf-8'))
    assert answer['tagline'] == 'You Know, for Search'


def test_es_search(es_enabled_app):
    entries = [{
            "code": 1,
            "name": "test1",
            "population": 3,
            "area": 30000,
            "density": 5,
            "municipality": [1]
        }, {
            "code": 2,
            "name": "test2",
            "population": 6,
            "area": 20000,
            "density": 5,
            "municipality": [1]
        }, {
            "code": 3,
            "name": "test3",
            "population": 4,
            "area": 50000,
            "density": 5,
            "municipality": [2, 3]
        }
    ]
    for entry in entries:
        es_enabled_app.post('/entry?resource=places',
                            data=json.dumps(entry),
                            content_type='application/json')

    time.sleep(1)

    with es_enabled_app.application.app_context():
        ids = search.search('places', 1, simple_query=None, extended_query='and|population|equals|3')
        assert len(ids) == 1
        assert ids[0]['population'] == 3
