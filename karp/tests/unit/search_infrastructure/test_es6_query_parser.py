import pytest

import elasticsearch_dsl as es_dsl

from karp.search.domain.query_dsl import (
    KarpQueryV6Parser,
    KarpQueryV6ModelBuilderSemantics,
)
from karp.search_infrastructure.queries.es6_search_service import EsQueryBuilder


@pytest.fixture(scope="session")
def parser() -> KarpQueryV6Parser:
    return KarpQueryV6Parser(semantics=KarpQueryV6ModelBuilderSemantics())


@pytest.mark.parametrize(
    "q,expected",
    [
        ("exists|test", es_dsl.Q("exists", field="test")),
        ("freetext|hej", es_dsl.Q("multi_match", query="hej", fuzziness=1)),
        ("freetext|12", es_dsl.Q("multi_match", query=12)),
        (
            "freergxp|1i.*2",
            es_dsl.Q("query_string", query="/1i.*2/", default_field="*"),
        ),
        ("missing|test", es_dsl.Q("bool", must_not=es_dsl.Q("exists", field="test"))),
        ("startswith|pos|nn", es_dsl.Q("regexp", pos="nn.*")),
        ("endswith|pos|nn", es_dsl.Q("regexp", pos=".*nn")),
        ("contains|pos|nn", es_dsl.Q("regexp", pos=".*nn.*")),
        ("gt|val|lok", es_dsl.Q("range", val={"gt": "lok"})),
        ("gte|val|2", es_dsl.Q("range", val={"gte": 2})),
        ("lt|val|lok", es_dsl.Q("range", val={"lt": "lok"})),
        ("lte|val|lok", es_dsl.Q("range", val={"lte": "lok"})),
        ("equals|pos|vb", es_dsl.Q("match", pos={"query": "vb", "operator": "and"})),
        ("regexp|kjh|lk.*k", es_dsl.Q("regexp", kjh="lk.*k")),
        ("not(regexp|kjh|lk.*k)", ~es_dsl.Q("regexp", kjh="lk.*k")),
        (
            "and(regexp|baseform|g[oe]t||equals|pos|nn)",
            es_dsl.Q("regexp", baseform="g[oe]t")
            & es_dsl.Q("match", pos={"query": "nn", "operator": "and"}),
        ),
        (
            "and(regexp|baseform|g[oe]t||equals|pos|nn||regexp|pos|n.*)",
            es_dsl.Q("regexp", baseform="g[oe]t")
            & es_dsl.Q("match", pos={"query": "nn", "operator": "and"})
            & es_dsl.Q("regexp", pos="n.*"),
        ),
        (
            "or(regexp|baseform|g[oe]t||equals|pos|nn)",
            es_dsl.Q("regexp", baseform="g[oe]t")
            | es_dsl.Q("match", pos={"query": "nn", "operator": "and"}),
        ),
        (
            "or(regexp|baseform|g[oe]t||equals|pos|nn||regexp|pos|n.*)",
            es_dsl.Q("regexp", baseform="g[oe]t")
            | es_dsl.Q("match", pos={"query": "nn", "operator": "and"})
            | es_dsl.Q("regexp", pos="n.*"),
        ),
        # (
        #     "regexp|or(pos||form)|k.+l",
        #     es_dsl.Q("regexp", pos="k.+l") | es_dsl.Q("regexp", form="k.+l")
        # ),
        # (
        #     "count(baseform)|gt|1",
        #     None,
        # )
    ],
)
def test_es_query(parser, q, expected):
    model = parser.parse(q)

    query = EsQueryBuilder().walk(model)

    assert query == expected


@pytest.mark.parametrize(
    "q,expected",
    [
        (
            "and(exists|pos||exists|vb)",
            es_dsl.Q(
                "bool",
                must=[
                    es_dsl.Q("exists", field="pos"),
                    es_dsl.Q("exists", field="vb"),
                ],
            ),
        ),
        (
            "or(exists|pos||exists|vb)",
            es_dsl.Q(
                "bool",
                should=[
                    es_dsl.Q("exists", field="pos"),
                    es_dsl.Q("exists", field="vb"),
                ],
            ),
        ),
        (
            "and(not(exists|pos)||not(exists|vb))",
            es_dsl.Q(
                "bool",
                must_not=[
                    es_dsl.Q("exists", field="pos"),
                    es_dsl.Q("exists", field="vb"),
                ],
            ),
        ),
        (
            "not(equals|ordklass|substantiv||equals|ordklass|verb)",
            es_dsl.Q(
                "bool",
                must_not=[
                    es_dsl.Q(
                        "match", ordklass={"query": "substantiv", "operator": "and"}
                    ),
                    es_dsl.Q("match", ordklass={"query": "verb", "operator": "and"}),
                ],
            ),
        ),
        #     (
        #         "exists|or(pos||vb)",
        #         es_dsl
        #         )
    ],
)
def test_combined_es_query(parser, q, expected):
    query = EsQueryBuilder().walk(parser.parse(q))

    assert query == expected
