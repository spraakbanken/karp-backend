import json
import pytest

places = [
    {
        'code': 3,
        'name': 'a',
        'municipality': [1]
    },
    {
        'code': 4,
        'name': 'b',
        'municipality': [2, 3]
    },
    {
        'code': 5,
        'name': 'c',
        'municipality': [2, 3],
        'larger_place': 4
    }
]


def init_diff_data(client_f, es_status_code):
    if es_status_code == 'skip':
        pytest.skip('elasticsearch disabled')
    client = client_f(use_elasticsearch=True)

    new_ids = []
    for entry in places:
        response = client.post('places/add',
                               data=json.dumps({'entry': entry}),
                               content_type='application/json')
        new_ids.append(json.loads(response.data.decode())['newID'])
    for i in range(1,10):
        for entry, entry_id in zip(places, new_ids):
            changed_entry = entry.copy()
            changed_entry['name'] = entry['name'] * i
            client.post('places/%s/update' % entry_id, data=json.dumps({
                'entry': changed_entry,
                'message': 'changes',
                'version': i
            }), content_type='application/json')

    return client


def test_diff(client_with_data_f, es):
    client = init_diff_data(client_with_data_f, es)

    response = client.get('places/3/diff?from_version=1&to_version=2')
    response_data = json.loads(response.data.decode())
    diff = response_data['diff']
    assert len(diff) == 1
    assert diff[0]['type'] == 'CHANGE'
    assert diff[0]['before'] == 'a'
    assert diff[0]['after'] == 'aa'
    assert diff[0]['field'] == 'name'
