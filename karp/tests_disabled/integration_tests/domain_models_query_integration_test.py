from itertools import zip_longest

import pytest  # pyre-ignore

from karp.domain import errors
from karp.domain.models.query import Query
from karp.query_dsl import op


@pytest.fixture
def query():
    return Query()


def test_empty_arg_and_empty_resource_str(query):
    with pytest.raises(errors.IncompleteQuery):
        query.parse_arguments({}, None)


def test_minimal(query):
    query.parse_arguments({"sort": "quiet"}, "saldo")
    assert isinstance(query.resources, list)
    assert len(query.resources) == 1
    assert query.resources[0] == "saldo"


def _test_nodes(r, facit):
    for x, f in zip_longest(r.gen_stream(), facit):
        assert x is not None, "x is too short"
        assert f is not None, "x is too long"

        assert x.type == f[0]
        assert x.value == f[1]
        assert isinstance(x.value, type(f[1]))


@pytest.mark.xfail(reason="look at this")
def test_rewrite_ast(fa_client_w_places_w_municipalities_scope_module):
    q = Query()
    q.parse_arguments({"q": "equals|state|X", "sort": "Y"}, "places")
    expected = [
        (op.EQUALS, None),
        (op.ARG_OR, None),
        (op.STRING, "state"),  # noqa: E131
        (op.STRING, "v_municipality.state"),
        (op.STRING, "X"),
    ]
    print("q.ast = {!r}".format(q.ast))
    _test_nodes(q.ast, expected)
