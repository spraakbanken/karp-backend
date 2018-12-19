import json
import pytest
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
    assert entries[0]['entry']['population'] == 5


def test_refs(es, client_with_data_f):
    client = init(client_with_data_f, es, [
        {
            'code': 1,
            'name': 'test1',
            'population': 10,
            'area': 50000,
            'density': 5,
            'municipality': [2, 3]
        },
        {
            'code': 2,
            'name': 'test2',
            'population': 5,
            'larger_place': 1,
            'area': 50000,
            'density': 5,
            'municipality': [2, 3]
        }
    ])

    # currently no connections are made on add/update, so we need to reindex to get the connections
    with client.application.app_context():
        import karp.resourcemgr as resourcemgr
        resource_id = 'places'
        version = 1
        index_name = resourcemgr.create_index(resource_id, version)
        resourcemgr.reindex(resource_id, index_name, version=version)
        resourcemgr.publish_index(resource_id, index_name)

    time.sleep(1)
    entries = get_json(client, 'places/_all_indexed')
    assert len(entries) == 2
    for entry in entries:
        if entry['code'] == 1:
            assert 'larger_place' not in entry
            assert 'smaller_places' in entry
            assert entry['smaller_places'][0]['code'] == 2
        else:
            assert entry['larger_place']['code'] == 1
            assert entry['larger_place']['name'] == 'test1'
            assert 'smaller_places' not in entry
