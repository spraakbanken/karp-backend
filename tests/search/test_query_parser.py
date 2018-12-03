from karp.search.query_parser import Query
from karp.search.query_parser import parse_query
from karp.search.query_parser import FreeText


def test_freetext():
    query: Query = parse_query('freetext|test')
    assert isinstance(query.query, FreeText)
