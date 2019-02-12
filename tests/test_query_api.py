import pytest  # pyre-ignore
import json
import time

ENTRIES = [{
    "code": 1,
    "name": "grund test",
    "population": 3122,
    "area": 30000,
    "density": 5,
    "municipality": [1]
}, {
    "code": 2,
    "name": "grunds",
    "population": 6312,
    "area": 20000,
    "density": 6,
    "municipality": [1]
}, {
    "code": 3,
    "name": "botten test",
    "population": 4132,
    "area": 50000,
    "density": 7,
    "municipality": [2, 3]
}
]


def get_json(client, path):
    response = client.get(path)
    return json.loads(response.data.decode())


def init(client, es_status_code, entries):
    if es_status_code == 'skip':
        pytest.skip('elasticsearch disabled')
    client_with_data = client(use_elasticsearch=True)

    for entry in entries:
        client_with_data.post('places/add',
                              data=json.dumps({'entry': entry}),
                              content_type='application/json')
    return client_with_data


def test_query_no_q(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    time.sleep(1)
    entries = get_json(client, 'places/query')
    assert len(entries['hits']) == 3
    assert entries['hits'][0]['entry']['name'] == 'grund test'


def test_freetext_string(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    time.sleep(1)
    entries = get_json(client, 'places/query?q=freetext|grund')
    assert len(entries['hits']) == 2
    assert entries['hits'][1]['entry']['name'] == 'grund test'
    assert entries['hits'][0]['entry']['name'] == 'grunds'


def test_freetext_integer(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    time.sleep(1)
    entries = get_json(client, 'places/query?q=freetext|3122')
    assert len(entries['hits']) == 1
    assert entries['hits'][0]['entry']['name'] == 'grund test'


def test_equals_string(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    time.sleep(1)
    entries = get_json(client, 'places/query?q=equals|name|grunds')
    assert len(entries['hits']) == 1
    assert entries['hits'][0]['entry']['name'] == 'grunds'


def test_equals_integer(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    time.sleep(1)
    entries = get_json(client, 'places/query?q=equals|density|7')
    assert len(entries['hits']) == 1
    assert entries['hits'][0]['entry']['name'] == 'botten test'


def test_freergxp_string(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    time.sleep(1)
    entries = get_json(client, 'places/query?q=freergxp|grunds?')
    assert len(entries['hits']) == 2
    assert entries['hits'][0]['entry']['name'] == 'grund test'
    assert entries['hits'][1]['entry']['name'] == 'grunds'


def test_and(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)
    entry = {
        "code": 4,
        "name": "botten test",
        "population": 4133,
        "area": 50000,
        "density": 7,
        "municipality": [2, 3]
    }
    client.post('places/add',
                data=json.dumps({'entry': entry}),
                content_type='application/json')

    time.sleep(1)
    query = 'and||equals|population|4133||equals|area|50000'
    entries = get_json(client, 'places/query?q=' + query)
    assert len(entries['hits']) == 1


def test_or(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    time.sleep(1)
    query = 'or||equals|population|6312||equals|population|4132'
    entries = get_json(client, 'places/query?q=' + query)
    assert len(entries['hits']) == 2


@pytest.mark.skip(reason="places doesn't exist")
def test_no_q(client):
    response = client.get('/places/query')
    assert response.status == '200 OK'
    assert response.status_code == 200
    json_data = response.get_json()
    assert "query_params" in json_data


@pytest.mark.skip(reason='no protected stuff')
def test_protected(client_with_data_scope_module):
    response = client_with_data_scope_module.get('/municipalities/query')
    assert response.status == '403 FORBIDDEN'


def test_pagination_explicit_0_25(es, client_with_data_f):
    client = init_data(client_with_data_f, es, 30)
    time.sleep(1)
    resource = 'places'
    response = client.get('/{}/query?from=0&size=25'.format(resource))
    assert response.status == '200 OK'
    assert response.is_json
    json_data = response.get_json()
    assert json_data
    assert 'hits' in json_data
    assert len(json_data['hits']) == 25


def test_pagination_explicit_13_45(es, client_with_data_f):
    client = init_data(client_with_data_f, es, 60)
    time.sleep(1)
    resource = 'places'
    response = client.get('/{}/query?from=13&size=45'.format(resource))
    assert response.status == '200 OK'
    assert response.is_json
    json_data = response.get_json()
    assert json_data
    assert 'hits' in json_data
    assert len(json_data['hits']) == 45


def test_pagination_default_size(es, client_with_data_f):
    client = init_data(client_with_data_f, es, 30)
    time.sleep(1)
    resource = 'places'
    response = client.get('/{}/query?from=0'.format(resource))
    assert response.status == '200 OK'
    assert response.is_json
    json_data = response.get_json()
    assert len(json_data['hits']) == 25


def test_pagination_default_from(es, client_with_data_f):
    client = init_data(client_with_data_f, es, 50)
    time.sleep(1)
    resource = 'places'
    response = client.get('/{}/query?size=45'.format(resource))
    assert response.status == '200 OK'
    assert response.is_json
    json_data = response.get_json()
    assert len(json_data['hits']) == 45


def test_pagination_fewer(es, client_with_data_f):
    client = init_data(client_with_data_f, es, 5)
    time.sleep(1)
    resource = 'places'
    response = client.get('/{}/query?from=10'.format(resource))
    assert response.status == '200 OK'
    assert response.is_json
    json_data = response.get_json()
    assert len(json_data['hits']) == 0


def init_data(client, es_status_code, no_entries):
    if es_status_code == 'skip':
        pytest.skip('elasticsearch disabled')
    client_with_data = client(use_elasticsearch=True)

    for i in range(0, no_entries):
        entry = {
            'code': i,
            'name': 'name',
            'municipality': [1]
        }
        client_with_data.post('places/add',
                              data=json.dumps({'entry': entry}),
                              content_type='application/json')
    return client_with_data
