import json

import pytest  # pyre-ignore


def get_json(client, path):
    print("Calling '{}' ...".format(path))
    response = client.get(path)
    assert 200 <= response.status_code < 300
    return json.loads(response.data.decode())


@pytest.mark.parametrize('endpoint', ['query', 'query_split'])
@pytest.mark.parametrize('query', [
    (''),
    ('freetext||eat my shorts'),
])
def test_distribution_in_result(client_with_entries_scope_session, query, endpoint):
    path = 'places/{endpoint}?{query}lexicon_stats=true'.format(
        endpoint=endpoint,
        query='q={}&'.format(query) if query else ''
    )
    result = get_json(client_with_entries_scope_session, path)

    assert 'distribution' in result
