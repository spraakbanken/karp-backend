from karp.api.query import QueryParameters, parse_arguments


def test_empty_arg():
    args = {}
    query_params = parse_arguments(args)
    
    assert isinstance(query_params, QueryParameters)
