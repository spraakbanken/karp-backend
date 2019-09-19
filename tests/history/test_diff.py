import json
import pytest  # pyre-ignore
from datetime import datetime, timezone
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


@pytest.fixture(scope='module')
def diff_data_client(client_with_data_f_scope_module, es):
    if es == 'skip':
        pytest.skip('elasticsearch disabled')
    client = client_with_data_f_scope_module(use_elasticsearch=True)

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
    assert response_data['from_version'] == 1
    assert response_data['to_version'] == 2


def test_diff2(diff_data_client):
    response = diff_data_client.get(
        'places/3/diff?from_date=%s&to_date=%s' %
        ('0', str(datetime.now(timezone.utc).timestamp()))
    )
    response_data = json.loads(response.data.decode())
    diff = response_data['diff']
    assert 'a' == diff[0]['before']
    assert 'aaaaaaaaa' == diff[0]['after']
    assert response_data['from_version'] == 1
    assert response_data['to_version'] == 9


def test_diff_from_first_to_date(diff_data_client):
    """
    this test is a bit shaky due to assuming that we will find the correct version by subtracting three seconds
    """
    response = diff_data_client.get('places/3/diff?to_date=%s' % (str(datetime.now(timezone.utc).timestamp() - 3)))
    response_data = json.loads(response.data.decode())
    diff = response_data['diff']
    assert 'a' == diff[0]['before']
    assert 'aaaaaaa' == diff[0]['after']
    assert response_data['from_version'] == 1
    assert response_data['to_version'] == 7


def test_diff_from_date_to_last(diff_data_client):
    """
        this test is a bit shaky due to assuming that we will find the correct version by subtracting three seconds
    """
    response = diff_data_client.get('places/3/diff?from_date=%s' % (str(datetime.now(timezone.utc).timestamp() - 3)))
    response_data = json.loads(response.data.decode())
    diff = response_data['diff']
    assert 'aaaaaaaa' == diff[0]['before']
    assert 'aaaaaaaaa' == diff[0]['after']
    assert response_data['from_version'] == 8
    assert response_data['to_version'] == 9


def test_diff_from_first_to_version(diff_data_client):
    response = diff_data_client.get('places/3/diff?to_version=7')
    response_data = json.loads(response.data.decode())
    diff = response_data['diff']
    assert 'a' == diff[0]['before']
    assert 'aaaaaaa' == diff[0]['after']
    assert response_data['from_version'] == 1
    assert response_data['to_version'] == 7


def test_diff_from_version_to_last(diff_data_client):
    response = diff_data_client.get('places/3/diff?from_version=7')
    response_data = json.loads(response.data.decode())
    diff = response_data['diff']
    assert 'aaaaaaa' == diff[0]['before']
    assert 'aaaaaaaaa' == diff[0]['after']
    assert response_data['from_version'] == 7
    assert response_data['to_version'] == 9


def test_diff_mix_version_date(diff_data_client):
    response = diff_data_client.get(
        'places/3/diff?from_version=2&to_date=%s' %
        str(datetime.now(timezone.utc).timestamp() - 3)
    )
    response_data = json.loads(response.data.decode())
    diff = response_data['diff']
    assert 'aa' == diff[0]['before']
    assert 'aaaaaaa' == diff[0]['after']
    assert response_data['from_version'] == 2
    assert response_data['to_version'] == 7


def test_diff_to_entry_data(diff_data_client):
    edited_entry = places[0].copy()
    edited_entry['name'] = 'testing'
    response = diff_data_client.get('places/3/diff?from_version=1',
                                    data=json.dumps(edited_entry),
                                    content_type='application/json')
    response_data = json.loads(response.data.decode())
    diff = response_data['diff']
    assert 'a' == diff[0]['before']
    assert 'testing' == diff[0]['after']
    assert response_data['from_version'] == 1
    assert 'to_version' not in response_data


def test_diff_no_flags(diff_data_client):
    response = diff_data_client.get('places/3/diff?from_version=1')
    response_data = json.loads(response.data.decode())
    diff = response_data['diff']
    assert 'a' == diff[0]['before']
    assert 'aaaaaaaaa' == diff[0]['after']
    assert response_data['from_version'] == 1
    assert response_data['to_version'] == 9
