import json
import time
import urllib.request
import urllib.parse
import pytest  # pyre-ignore
from karp.search import search

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


def init(client, es_status_code):
    client_with_data = client(use_elasticsearch=True)
    if es_status_code == 'skip':
        pytest.skip("elasticsearch disabled")

    for entry in entries:
        client_with_data.post('places/add',
                              data=json.dumps({'entry': entry}),
                              content_type='application/json')
    return client_with_data


def test_es_setup(es):
    if es == 'skip':
        pytest.skip("elasticsearch disabled")

    url = 'http://localhost:9201'
    f = urllib.request.urlopen(url)
    answer = json.loads(f.read().decode('utf-8'))
    assert answer['tagline'] == 'You Know, for Search'


def test_es_search(es, client_with_data_f):
    client_with_data = init(client_with_data_f, es)

    time.sleep(1)

    with client_with_data.application.app_context():
        query = search.get_query('and|population|equals|3')
        ids = search.search(['places'], {'query': query, 'split_results': False})
        assert len(ids) == 1
        assert ids[0]['population'] == 3


def test_es_search2(es, client_with_data_f):
    client_with_data = init(client_with_data_f, es)

    time.sleep(1)

    with client_with_data.application.app_context():
        query = search.get_query('and|population|equals|3')
        result = search.search(['places', 'municipalities'], {'query': query, 'split_results': True})
        assert 'places' in result
        assert 'municipalities' in result
        assert len(result['municipalities']) == 0
        assert len(result['places']) == 1
