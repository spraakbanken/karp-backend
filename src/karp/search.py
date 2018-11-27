from flask import current_app
from elasticsearch_dsl import Search, Q


def search(resource_id, version, simple_query=None, extended_query=None):
    s = Search(using=current_app.elasticsearch)

    if simple_query:
        s = s.query("match", _all=simple_query)

    if extended_query:
        s = s.query(_map_extended_to_query(resource_id, version, extended_query))

    s = s.index(resource_id + '_' + str(version))
    response = s.execute()
    return [result.meta.id for result in response]


def _map_extended_to_query(resource_id, version, extended_query):
    # Only handle simplest case, for example: 'and|baseform.search|equals|userinput'
    [_, field, op, querystr] = extended_query.split('|')

    # some TODO s
    # 1. Need to check config if the field search must be nested https://www.elastic.co/guide/en/elasticsearch/reference/current/nested.html
    # 2. Maybe need to map query input to another field in ES

    return Q("term", **{field: querystr})
