import pytest
import json


def get_json(client, path):
    response = client.get(path)
    return json.loads(response.data.decode())


def init(client, es_status_code):
    if es_status_code == 'skip':
        pytest.skip('elasticsearch disabled')
    return client(use_elasticsearch=True)


def test_add(es, client_with_data_f):
    client = init(client_with_data_f, es)

    entry = {
        'code': 1,
        'name': '1',
        'municipality': [1]
    }
    client.post('places/add',
                data=json.dumps({'entry': entry}),
                content_type='application/json')

    result = get_json(client, 'places/query')
    assert result['hits'][0]['version'] == 1


def test_no_changes_update(es, client_with_data_f):
    client = init(client_with_data_f, es)

    entry = {
        'code': 1,
        'name': '1',
        'municipality': [1]
    }
    client.post('places/add',
                data=json.dumps({'entry': entry}),
                content_type='application/json')

    client.post('places/1/update', data=json.dumps({
        'entry': entry,
        'message': 'message',
        'version': 1
    }), content_type='application/json')

    result = get_json(client, 'places/query')
    assert result['hits'][0]['version'] == 1


def test_update(es, client_with_data_f):
    client = init(client_with_data_f, es)

    entry = {
        'code': 1,
        'name': '1',
        'municipality': [1]
    }
    client.post('places/add',
                data=json.dumps({'entry': entry}),
                content_type='application/json')

    entry['name'] = '2'
    client.post('places/1/update', data=json.dumps({
        'entry': entry,
        'message': 'message',
        'version': 1
    }), content_type='application/json')

    result = get_json(client, 'places/query')
    assert result['hits'][0]['version'] == 2

    result = get_json(client, 'places/query?split_results=true')
    assert result['places']['hits'][0]['version'] == 2


def test_conflict(es, client_with_data_f):
    client = init(client_with_data_f, es)

    entry = {
        'code': 1,
        'name': '1',
        'municipality': [1]
    }
    client.post('places/add',
                data=json.dumps({'entry': entry}),
                content_type='application/json')

    entry['name'] = '2'
    client.post('places/1/update', data=json.dumps({
        'entry': entry,
        'message': 'message',
        'version': 1
    }), content_type='application/json')

    entry['name'] = '1'

    response = client.post('places/1/update', data=json.dumps({
        'entry': entry,
        'message': 'message',
        'version': 1
    }), content_type='application/json')

    assert response.status_code == 400
    assert 'Version' in json.loads(response.data.decode())['error']


def test_delete(es, client_with_data_f):
    client = init(client_with_data_f, es)

    entry = {
        'code': 1,
        'name': '1',
        'municipality': [1]
    }
    client.post('places/add',
                data=json.dumps({'entry': entry}),
                content_type='application/json')

    client.delete('places/1/delete')

    # TODO query history about changes, when we have a history api


def test_reindex(es, client_with_data_f):
    client = init(client_with_data_f, es)

    entry = {
        'code': 1,
        'name': '1',
        'municipality': [1]
    }
    client.post('places/add',
                data=json.dumps({'entry': entry}),
                content_type='application/json')

    for i in range(2, 10):
        entry['name'] = str(i)
        client.post('places/1/update', data=json.dumps({
            'entry': entry,
            'message': 'message',
            'version': i
        }), content_type='application/json')

    with client.application.app_context():
        import karp.indexmgr as indexmgr
        indexmgr.publish_index('places')

    result = get_json(client, 'places/query')
    assert result['hits'][0]['version'] == 9
    assert len(result['hits']) == 1
