import pytest  # pyre-ignore
import json
import time


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
    client = init(client_with_data_f, es, [])

    client.post('places/add', data=json.dumps({
        'entry': {
            'code': 3,
            'name': 'test3',
            'population': 4,
            'area': 50000,
            'density': 5,
            'municipality': [2, 3]
        }
    }), content_type='application/json')

    # currently no connections are made on add/update, so we need to reindex to get the connections
    with client.application.app_context():
        import karp.indexmgr as indexmgr
        resource_id = 'places'
        version = 1
        index_name = indexmgr.create_index(resource_id, version)
        indexmgr.reindex(resource_id, index_name, version=version)
        indexmgr.publish_index(resource_id, index_name)

    time.sleep(1)
    entries = get_json(client, 'places/query')
    assert len(entries) == 1
    assert entries[0]['entry']['name'] == 'test3'


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
