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
                              data=json.dumps({'entry': entry}),
                              content_type='application/json')
    return client_with_data


def test_add(es, client_with_data_f):
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

    client.delete('places/%s/delete' % entry_id)

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

    client.post('places/%s/update' % entry_id, data=json.dumps({
        'entry': {
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

    time.sleep(1)
    entries = get_json(client, 'places/_all_indexed')
    assert len(entries) == 2
    for val in entries:
        assert 'entry' in val
        entry = val['entry']
        print('entry = {}'.format(entry))
        if entry['code'] == 1:
            assert '_larger_place' not in entry
            assert 'larger_place' not in entry
            assert '_smaller_places' in entry
            assert entry['_smaller_places'][0]['code'] == 2
        else:
            assert entry['_larger_place']['code'] == 1
            assert entry['_larger_place']['name'] == 'test1'
            assert '_smaller_places' not in entry


def test_external_refs(es, client_with_data_f):
    client = init(client_with_data_f, es, [
        {
            'code': 1,
            'name': 'test1',
            'population': 10,
            'area': 50000,
            'density': 5,
            'municipality': [1]
        },
        {
            'code': 2,
            'name': 'test2',
            'population': 5,
            'larger_place': 1,
            'area': 50000,
            'density': 5,
            'municipality': [1, 2]
        },
        {
            'code': 3,
            'name': 'test2',
            'population': 5,
            'larger_place': 1,
            'area': 50000,
            'density': 5,
            'municipality': [2]
        }
    ])

    client.post('municipalities/add',
                data=json.dumps({
                    'entry': {
                        'code': 1,
                        'name': 'municipality1',
                        'state': 'state1',
                        'region': 'region1'
                    }
                }),
                content_type='application/json')

    client.post('municipalities/add',
                data=json.dumps({
                    'entry': {
                        'code': 2,
                        'name': 'municipality2',
                        'state': 'state2',
                        'region': 'region2'
                    }
                }),
                content_type='application/json')

    time.sleep(1)
    entries = get_json(client, 'municipalities/_all_indexed')
    for val in entries:
        assert 'entry' in val
        entry = val['entry']

        assert '_places' in entry
        place_codes = [place['code'] for place in entry['_places']]
        assert len(place_codes) == 2
        if entry['code'] == 1:
            assert 1 in place_codes
            assert 2 in place_codes
        else:
            assert 2 in place_codes
            assert 3 in place_codes

    places_entries = get_json(client, 'places/_all_indexed')
    for val in places_entries:
        assert 'entry' in val
        entry = val['entry']
        assert 'municipality' in entry
        assert isinstance(entry['_municipality'], list)
        if entry['code'] == 2:
            assert {'code': 1, 'name': 'municipality1', 'state': 'state1'} in entry['_municipality']
            assert {'code': 2, 'name': 'municipality2', 'state': 'state2'} in entry['_municipality']


def test_update_refs(es, client_with_data_f):
    client = init(client_with_data_f, es, [
        {
            'code': 5,
            'name': 'test1',
            'population': 10,
            'area': 50000,
            'density': 5,
            'municipality': [2, 3]
        },
        {
            'code': 6,
            'name': 'test2',
            'population': 5,
            'larger_place': 5,
            'area': 50000,
            'density': 5,
            'municipality': [2, 3]
        }
    ])

    time.sleep(1)
    entries = get_json(client, 'places/_all_indexed')
    assert len(entries) == 2
    for val in entries:
        assert 'entry' in val
        entry = val['entry']
        print('entry = {}'.format(entry))
        if entry['code'] == 5:
            assert '_smaller_places' in entry
            assert entry['_smaller_places'][0]['code'] == 6

    client.delete('/places/6/delete')

    time.sleep(1)
    entries = get_json(client, 'places/_all_indexed')
    assert len(entries) == 1
    entry = entries[0]
    assert '_smaller_places' not in entry
