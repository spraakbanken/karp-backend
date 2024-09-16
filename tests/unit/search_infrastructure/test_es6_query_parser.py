import pytest  # noqa: I001

import elasticsearch_dsl as es_dsl

from karp.search.domain.query_dsl.karp_query_v6_parser import KarpQueryV6Parser
from karp.search.domain.query_dsl.karp_query_v6_model import (
    KarpQueryV6ModelBuilderSemantics,
)
from karp.search.infrastructure.es import EsQueryBuilder


@pytest.fixture(scope="session")
def parser() -> KarpQueryV6Parser:
    return KarpQueryV6Parser(semantics=KarpQueryV6ModelBuilderSemantics())


class MappingRepo:
    """
    For these query parser tests, infT means that the field is nested, no matter
    where in the hierachy it appears
    """

    def __init__(self):
        pass

    def is_nested(self, resource_id, field):
        return field.endswith("infT")

    def get_nested_fields(self, _):
        return ["infT"]


def es_query_builder():
    mapping_repo = MappingRepo()
    return EsQueryBuilder("r", mapping_repo)


@pytest.mark.parametrize(
    "q,expected",
    [
        ("exists|test", es_dsl.Q("exists", field="test")),
        (
            'freetext|"hej"',
            es_dsl.Q(
                "bool",
                should=[
                    es_dsl.Q("multi_match", query="hej", fields=["*"], lenient=True),
                    es_dsl.Q(
                        "nested",
                        path="infT",
                        query=es_dsl.Q(
                            "multi_match", query="hej", fields=["infT.*"], lenient=True
                        ),
                    ),
                ],
            ),
        ),
        (
            'freergxp|"1i.*2"',
            es_dsl.Q(
                "bool",
                should=[
                    es_dsl.Q("query_string", query="/1i.*2/", fields=["*"], lenient=True),
                    es_dsl.Q(
                        "nested",
                        path="infT",
                        query=es_dsl.Q(
                            "query_string", query="/1i.*2/", fields=["infT.*"], lenient=True
                        ),
                    ),
                ],
            ),
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
            r'and(regexp|name|"\s")',
            es_dsl.Q("regexp", name="\\s"),
        ),
        (
            "infT(and(equals|wf|a||equals|msd|s))",
            es_dsl.Q(
                "nested",
                path="infT",
                query=(
                    es_dsl.Q("match", infT__wf={"query": "a", "operator": "and"})
                    & es_dsl.Q("match", infT__msd={"query": "s", "operator": "and"})
                ),
            ),
        ),
        (
            "t1(equals|infT.wf|word)",
            es_dsl.Q(
                "nested",
                path="t1.infT",
                query=es_dsl.Q("match", t1__infT__wf={"query": "word", "operator": "and"}),
            ),
        ),
        (
            "t1(infT(equals|wf|word))",
            es_dsl.Q(
                "nested",
                path="t1.infT",
                query=es_dsl.Q("match", t1__infT__wf={"query": "word", "operator": "and"}),
            ),
        ),
    ],
)
def test_es_query(parser, q, expected):
    model = parser.parse(q)

    query = es_query_builder().walk(model)

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
    query = es_query_builder().walk(parser.parse(q))

    assert query == expected


@pytest.mark.parametrize(
    "q1,q2",
    [
        (
            "equals|infT.wf|word",
            "infT(equals|wf|word)",
        ),
        (
            "equals|t1.infT.wf|word",
            "t1(infT(equals|wf|word))",
        ),
        (
            "t1(equals|infT.wf|word)",
            "t1(infT(equals|wf|word))",
        ),
        (
            "t1.infT(equals|wf|word)",
            "t1(infT(equals|wf|word))",
        ),
    ],
)
def test_sub_query_rewrite(parser, q1, q2):
    assert es_query_builder().walk(parser.parse(q1)) == es_query_builder().walk(parser.parse(q2))
