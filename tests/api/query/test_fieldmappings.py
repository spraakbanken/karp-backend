import json

import pytest

from elasticsearch_dsl.query import Bool, Exists, Match, Range, Regexp

from karp.search import search
from karp.elasticsearch.search import EsQuery


def get_json(client, path):
    print("Calling '{}' ...".format(path))
    response = client.get(path)
    assert 200 <= response.status_code < 300
    return json.loads(response.data.decode())


@pytest.mark.parametrize('resource,query,expected_hits', [
    ('places', 'equals|state|västerbottens', 6),
    ('places,municipalities', 'equals|state|västerbottens', 7),
    ('municipalities', 'gt|population|42108', 1),
    ('municipalities,places', 'lt|population|4133', 5),
    ('places', 'contains||or|state|name||st', 7),
    ('places', 'contains||and|state|name||st', 1),
    ('places', 'equals||and|state|name||st', 0),
    ('places', 'and||startswith|state|Norr||equals|area|6312', 4),
    ('places', 'or||startswith|state|Norr||equals|area|6312', 8),
    ('places', 'not||startswith|state|Norr||equals|area|6312', 1),
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


@pytest.mark.parametrize('resources,query,expected', [
    # ('places', 'equals|state|västerbottens', 6),
    # ('places,municipalities', 'equals|state|västerbottens', 7),
    # ('municipalities', 'gt|population|42108', 1),
    # ('municipalities,places', 'lt|population|4133', 5),
    # ('places', 'contains||or|state|name||st', 7),
    (
        'places',
        'contains||and|state|name||st',
        Bool(must=[
            Bool(should=[Regexp(name='.*st.*'), Regexp(name__raw='.*st.*')]),
            Bool(should=[
                Bool(should=[Regexp(state='.*st.*'), Regexp(state__raw='.*st.*')]),
                Bool(should=[Regexp(v_municipality__state='.*st.*'), Regexp(v_municipality__state__raw='.*st.*')]),
            ])
        ])
    ),
    (
        'places',
        'equals||and|state|name||st',
        Bool(must=[
            Match(name={"query": "st", "operator": "and"}),
            Bool(should=[
                Match(state={"query": "st", "operator": "and"}),
                Match(v_municipality__state={"query": "st", "operator": "and"}),
            ]),
        ])
    ),
    (
        'places',
        'lt||and|state|name||st',
        Bool(must=[
            Range(name={"lt": "st"}),
            Bool(should=[
                Range(state={"lt": "st"}),
                Range(v_municipality__state={"lt": "st"}),
            ]),
        ])
    ),
    (
        'municipalities',
        'gt|population|42108',
        Bool(should=[
            Range(population={"gt": 42108}),
            Range(population__value__total={"gt": 42108}),
        ])
    ),
    (
        'places',
        'exists|state',
        Bool(should=[
            Exists(field="state"),
            Exists(field="v_municipality.state")
        ])
    ),
    # ('places', 'and||startswith|state|Norr||equals|area|6312', 4),
    # ('places', 'or||startswith|state|Norr||equals|area|6312', 8),
    # ('places', 'not||startswith|state|Norr||equals|area|6312', 1),
])
def test_build_query_field_mapping(client_with_entries_scope_session, resources, query, expected):
    args = {}
    if query:
        args["q"] = query
    q = search.build_query(args, resources)

    print("q = {q}".format(q=q))
    assert isinstance(q, EsQuery)
    assert q.query == expected
