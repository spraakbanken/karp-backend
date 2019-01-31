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
    assert len(entries) == 3
    assert entries[0]['entry']['name'] == 'grund test'


def test_freetext_string(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    time.sleep(1)
    entries = get_json(client, 'places/query?q=freetext|grund')
    assert len(entries) == 2
    assert entries[1]['entry']['name'] == 'grund test'
    assert entries[0]['entry']['name'] == 'grunds'


def test_freetext_integer(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    time.sleep(1)
    entries = get_json(client, 'places/query?q=freetext|3122')
    assert len(entries) == 1
    assert entries[0]['entry']['name'] == 'grund test'


def test_equals_string(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    time.sleep(1)
    entries = get_json(client, 'places/query?q=equals|name|grunds')
    assert len(entries) == 1
    assert entries[0]['entry']['name'] == 'grunds'


def test_equals_integer(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    time.sleep(1)
    entries = get_json(client, 'places/query?q=equals|density|7')
    assert len(entries) == 1
    assert entries[0]['entry']['name'] == 'botten test'


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


@pytest.mark.skip(reason="places doesn't exist")
def test_pagination_explicit_0_25(client):
    resource = 'places'
    response = client.get('/{}/query?from=0&size=25'.format(resource))
    assert response.status == '200 OK'
    assert response.is_json
    json_data = response.get_json()
    assert json_data
    assert resource in json_data
    assert 'hits' in json_data[resource]
    assert len(json_data[resource]['hits']) == 25


@pytest.mark.skip(reason="places doesn't exist")
def test_pagination_explicit_13_45(client):
    resource = 'places'
    response = client.get('/{}/query?from=13&size=45'.format(resource))
    assert response.status == '200 OK'
    assert response.is_json
    json_data = response.get_json()
    assert json_data
    assert resource in json_data
    assert 'hits' in json_data[resource]
    assert len(json_data[resource]['hits']) == 45


@pytest.mark.skip(reason="places doesn't exist")
def test_pagination_default_size(client):
    resource = 'places'
    response = client.get('/{}/query?from=0'.format(resource))
    assert response.status == '200 OK'
    assert response.is_json
    json_data = response.get_json()
    assert len(json_data[resource]['hits']) == 25


@pytest.mark.skip(reason="places doesn't exist")
def test_pagination_default_from(client):
    resource = 'places'
    response = client.get('/{}/query?size=45'.format(resource))
    assert response.status == '200 OK'
    assert response.is_json
    json_data = response.get_json()
    assert len(json_data[resource]['hits']) == 45
