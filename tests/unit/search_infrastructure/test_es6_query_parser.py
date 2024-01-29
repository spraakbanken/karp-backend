import pytest  # noqa: I001

import elasticsearch_dsl as es_dsl

from karp.search.domain.query_dsl.karp_query_v6_parser import KarpQueryV6Parser
from karp.search.domain.query_dsl.karp_query_v6_model import (
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
        ('freetext|"hej"', es_dsl.Q("multi_match", query="hej")),
        (
            'freergxp|"1i.*2"',
            es_dsl.Q("query_string", query="/1i.*2/", default_field="*"),
        ),
        ("missing|test", es_dsl.Q("bool", must_not=es_dsl.Q("exists", field="test"))),
        ('startswith|pos|"nn"', es_dsl.Q("regexp", pos="nn.*")),
        ('endswith|pos|"nn"', es_dsl.Q("regexp", pos=".*nn")),
        ('contains|pos|"nn"', es_dsl.Q("regexp", pos=".*nn.*")),
        ('gt|val|"lok"', es_dsl.Q("range", val={"gt": "lok"})),
        ("gte|val|2", es_dsl.Q("range", val={"gte": 2})),
        ('lt|val|"lok"', es_dsl.Q("range", val={"lt": "lok"})),
        ('lte|val|"lok"', es_dsl.Q("range", val={"lte": "lok"})),
        ('equals|pos|"vb"', es_dsl.Q("match", pos={"query": "vb", "operator": "and"})),
        ('regexp|kjh|"lk.*k"', es_dsl.Q("regexp", kjh="lk.*k")),
        ('not(regexp|kjh|"lk.*k")', ~es_dsl.Q("regexp", kjh="lk.*k")),
        (
            'and(regexp|baseform|"g[oe]t"||equals|pos|"nn")',
            es_dsl.Q("regexp", baseform="g[oe]t")
            & es_dsl.Q("match", pos={"query": "nn", "operator": "and"}),
        ),
        (
            'and(regexp|baseform|"g[oe]t"||equals|pos|"nn"||regexp|pos|"n.*")',
            es_dsl.Q("regexp", baseform="g[oe]t")
            & es_dsl.Q("match", pos={"query": "nn", "operator": "and"})
            & es_dsl.Q("regexp", pos="n.*"),
        ),
        (
            'or(regexp|baseform|"g[oe]t"||equals|pos|"nn")',
            es_dsl.Q("regexp", baseform="g[oe]t")
            | es_dsl.Q("match", pos={"query": "nn", "operator": "and"}),
        ),
        (
            'or(regexp|baseform|"g[oe]t"||equals|pos|"nn"||regexp|pos|"n.*")',
            es_dsl.Q("regexp", baseform="g[oe]t")
            | es_dsl.Q("match", pos={"query": "nn", "operator": "and"})
            | es_dsl.Q("regexp", pos="n.*"),
        ),
        (
            'equals|baseform|"t|est"',
            es_dsl.Q("match", baseform={"query": "t|est", "operator": "and"}),
        ),
        (
            'equals|baseform|"|test"',
            es_dsl.Q("match", baseform={"query": "|test", "operator": "and"}),
        ),
        (
            'equals|baseform|"test|"',
            es_dsl.Q("match", baseform={"query": "test|", "operator": "and"}),
        ),
        (
            'and(equals|ortografi|"ständigt förknippad")',
            es_dsl.Q("match", ortografi={"query": "ständigt förknippad", "operator": "and"}),
        ),
        (
            'and(equals|ortografi|"(ständigt) förknippad")',
            es_dsl.Q("match", ortografi={"query": "(ständigt) förknippad", "operator": "and"}),
        ),
        (
            'and(equals|ortografi|"(ständigt förknippad")',
            es_dsl.Q("match", ortografi={"query": "(ständigt förknippad", "operator": "and"}),
        ),
        # escaped quotes
        (
            'and(equals|baseform|"att \\"vara\\"")',
            es_dsl.Q("match", baseform={"query": 'att "vara"', "operator": "and"}),
        ),
        # no quotes work
        (
            "and(equals|baseform|noquotes)",
            es_dsl.Q("match", baseform={"query": "noquotes", "operator": "and"}),
        ),
        (
            'and(regexp|name|"\s")',
            es_dsl.Q("regexp", name="\\s"),
        ),
    ],
)
def test_es_query(parser, q, expected):  # noqa: ANN201
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
            'not(equals|ordklass|"substantiv"||equals|ordklass|"verb")',
            es_dsl.Q(
                "bool",
                must_not=[
                    es_dsl.Q("match", ordklass={"query": "substantiv", "operator": "and"}),
                    es_dsl.Q("match", ordklass={"query": "verb", "operator": "and"}),
                ],
            ),
        ),
    ],
)
def test_combined_es_query(parser, q, expected):  # noqa: ANN201
    query = EsQueryBuilder().walk(parser.parse(q))

    assert query == expected
