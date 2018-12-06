import json
import pytest


def get_json(client, path):
    response = client.get(path)
    return json.loads(response.data.decode())


def init(client, es_status_code, entries):
    if es_status_code == 'skip':
        pytest.skip('elasticsearch disabled')
    client_with_data = client(use_elasticsearch=True)

    for entry in entries:
        client_with_data.post('places/add',
                              data=json.dumps(entry),
                              content_type='application/json')
    return client_with_data


def test_add(es, client_with_data_f):
    client = init(client_with_data_f, es, [])

    client.post('places/add', data=json.dumps({
        'code': 3,
        'name': 'test3',
        'population': 4,
        'area': 50000,
        'density': 5,
        'municipality': [2, 3]
    }), content_type='application/json')

    entries = get_json(client, 'places/_all')
    assert len(entries) == 1
    assert entries[0]['entry']['name'] == 'test3'


def test_delete(es, client_with_data_f):
    client = init(client_with_data_f, es, [{
        'code': 3,
        'name': 'test3',
        'population': 4,
        'area': 50000,
        'density': 5,
        'municipality': [2, 3]
    }])

    entries = get_json(client, 'places/_all')
    entry_id = entries[0]['id']

    client.delete('places/delete/%s' % entry_id)

    entries = get_json(client, 'places/_all')
    assert len(entries) == 0


def test_update(es, client_with_data_f):
    client = init(client_with_data_f, es, [{
        'code': 3,
        'name': 'test3',
        'population': 4,
        'area': 50000,
        'density': 5,
        'municipality': [2, 3]
    }])

    entries = get_json(client, 'places/_all')
    entry_id = entries[0]['id']

    client.post('places/update/%s' % entry_id, data=json.dumps({
        'doc': {
            'code': 3,
            'name': 'test3',
            'population': 5,
            'area': 50000,
            'density': 5,
            'municipality': [2, 3]
        },
        'message': 'changes'
    }), content_type='application/json')

    entries = get_json(client, 'places/_all')
    assert len(entries) == 1
    assert entries[0]['id'] == entry_id
