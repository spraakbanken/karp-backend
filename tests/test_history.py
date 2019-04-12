import json
import pytest
from datetime import datetime
import time

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


@pytest.fixture
def diff_data_client(client_with_data_f, es):
    if es == 'skip':
        pytest.skip('elasticsearch disabled')
    client = client_with_data_f(use_elasticsearch=True)

    response = client.post('places/add',
                           data=json.dumps({'entry': places[0]}),
                           content_type='application/json')
    new_id = json.loads(response.data.decode())['newID']
    time.sleep(1)
    for i in range(2, 10):
        changed_entry = places[0].copy()
        changed_entry['name'] = places[0]['name'] * i
        client.post('places/%s/update' % new_id, data=json.dumps({
            'entry': changed_entry,
            'message': 'changes',
            'version': i - 1
        }), content_type='application/json')
        time.sleep(1)

    return client


def test_diff1(diff_data_client):
    response = diff_data_client.get('places/3/diff?from_version=1&to_version=2')
    response_data = json.loads(response.data.decode())
    diff = response_data['diff']
    assert len(diff) == 1
    assert 'CHANGE' == diff[0]['type']
    assert 'a' == diff[0]['before']
    assert 'aa' == diff[0]['after']
    assert 'name' == diff[0]['field']


def test_diff2(diff_data_client):
    response = diff_data_client.get('places/3/diff?from_date=%s&to_date=%s' % ('0', str(datetime.now().timestamp())))
    response_data = json.loads(response.data.decode())
    diff = response_data['diff']
    assert 1 == len(diff)
    assert 'CHANGE' == diff[0]['type']
    assert 'a' == diff[0]['before']
    assert 'aaaaaaaaa' == diff[0]['after']
    assert 'name' == diff[0]['field']


def test_diff_from_first_to_date(diff_data_client):
    """
    this test is a bit shaky due to assuming that we will find the correct version by subtracting three seconds
    """
    response = diff_data_client.get('places/3/diff?to_date=%s' % (str(datetime.now().timestamp() - 3)))
    response_data = json.loads(response.data.decode())
    diff = response_data['diff']
    assert 1 == len(diff)
    assert 'CHANGE' == diff[0]['type']
    assert 'a' == diff[0]['before']
    assert 'aaaaaaa' == diff[0]['after']
    assert 'name' == diff[0]['field']


def test_diff_from_date_to_last(diff_data_client):
    """
        this test is a bit shaky due to assuming that we will find the correct version by subtracting three seconds
    """
    response = diff_data_client.get('places/3/diff?from_date=%s' % (str(datetime.now().timestamp() - 3)))
    response_data = json.loads(response.data.decode())
    diff = response_data['diff']
    assert 1 == len(diff)
    assert 'CHANGE' == diff[0]['type']
    assert 'aaaaaaaa' == diff[0]['before']
    assert 'aaaaaaaaa' == diff[0]['after']
    assert 'name' == diff[0]['field']


def test_diff_from_first_to_version(diff_data_client):
    response = diff_data_client.get('places/3/diff?to_version=7')
    response_data = json.loads(response.data.decode())
    diff = response_data['diff']
    assert 1 == len(diff)
    assert 'CHANGE' == diff[0]['type']
    assert 'a' == diff[0]['before']
    assert 'aaaaaaa' == diff[0]['after']
    assert 'name' == diff[0]['field']


def test_diff_from_version_to_last(diff_data_client):
    response = diff_data_client.get('places/3/diff?from_version=7')
    response_data = json.loads(response.data.decode())
    diff = response_data['diff']
    assert 1 == len(diff)
    assert 'CHANGE' == diff[0]['type']
    assert 'aaaaaaa' == diff[0]['before']
    assert 'aaaaaaaaa' == diff[0]['after']
    assert 'name' == diff[0]['field']
