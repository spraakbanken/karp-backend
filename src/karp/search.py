from typing import Dict, List

from flask import current_app # pyre-ignore
from elasticsearch_dsl import Search, Q # pyre-ignore


def search(resource_id: str, version: int, simple_query=None, extended_query=None) -> List[Dict[str, Dict]]:
    s = Search(using=current_app.elasticsearch)

    if simple_query:
        s = s.query("match", _all=simple_query)

    if extended_query:
        s = s.query(_map_extended_to_query(resource_id, version, extended_query))

    s = s.index(resource_id + '_' + str(version))
    response = s.execute()
    return [result.to_dict() for result in response]


def _map_extended_to_query(resource_id: str, version: int, extended_query: str):
    # Only handle simplest case, for example: 'and|baseform.search|equals|userinput'
    [_, field, op, query_str] = extended_query.split('|')

    # some TODO s
    # 1. Need to check config if the field search must be nested
    # https://www.elastic.co/guide/en/elasticsearch/reference/current/nested.html
    # 2. Maybe need to map query input to another field in ES

    return Q("term", **{field: query_str})
