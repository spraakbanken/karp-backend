import json

import pytest


def get_json(client, path):
    print("Calling '{}' ...".format(path))
    response = client.get(path)
    assert 200 <= response.status_code < 300
    return json.loads(response.data.decode())


@pytest.mark.parametrize('resource,query,expected_hits', [
    ('places', 'equals|state|västerbottens', 7),
    ('municipalities', 'gt|population|42108', 1),
    ('places', 'contains||or|state|name||botten', 5),
])
def test_query_field_mapping(client_with_entries_scope_session, resource, query, expected_hits):
    path = '{resource}/query?{query}'.format(
        resource=resource,
        query='q={}'.format(query) if query else ''
    )
    result = get_json(client_with_entries_scope_session, path)

    assert 'hits' in result
    print("result['hits'] = {result[hits]}".format(result=result))
    assert len(result['hits']) == expected_hits
