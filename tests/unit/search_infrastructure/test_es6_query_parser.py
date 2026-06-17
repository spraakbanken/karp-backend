import pytest  # noqa: I001

import opensearchpy
from karp.globals import os_client
from karp.search.domain.query_dsl.karp_query_parser import KarpQueryParser
from karp.search.domain.query_dsl.karp_query_model import KarpQueryModelBuilderSemantics
from karp.search.infrastructure.opensearch.search_service import EsQueryBuilder


@pytest.fixture(scope="session")
def parser() -> KarpQueryParser:
    return KarpQueryParser(semantics=KarpQueryModelBuilderSemantics())


def es_query_builder():
    class MockAliases:
        def aliases(self, *_args, **_kwargs):
            return "r r\n1"

    class MockIndices:
        def get_mapping(self):
            infT = {
                "type": "nested",
                "properties": {
                    "wf": {"type": "text"},
                    "msd": {"type": "text"},
                    "variant": {"type": "boolean"},
                },
            }
            return {
                "r": {
                    "mappings": {
                        "properties": {
                            "t1": {
                                "type": "object",
                                "properties": {"infT": infT},
                            },
                            "infT": infT,
                            "ordklass": {"type": "text"},
                            "pos": {"type": "text"},
                            "vb": {"type": "text"},
                            "ortografi": {"type": "text"},
                            "name": {"type": "text"},
                            "baseform": {"type": "text"},
                            "kjh": {"type": "text"},
                            "val": {"type": "text"},
                            "test": {"type": "text"},
                        }
                    }
                }
            }

    class MockEs:
        def __init__(self):
            self.cat = MockAliases()
            self.indices = MockIndices()

    es_obj = MockEs()
    os_client.ctx_var.set(es_obj)
    return EsQueryBuilder("r")


def get_regexp_object(field, val):
    return opensearchpy.Q(
        "query_string",
        query=f"/{val}/",
        fields=[field],
        lenient=True,
    )


@pytest.mark.parametrize(
    "q,expected",
    [
        ("exists|test", opensearchpy.Q("exists", field="test")),
        (
            'infT(freetext|"hej")',
            opensearchpy.Q(
                "nested",
                path="infT",
                query=opensearchpy.Q(
                    "bool",
                    should=[
                        opensearchpy.Q("match_phrase", **{"infT.wf": "hej"}),
                        opensearchpy.Q("match_phrase", **{"infT.msd": "hej"}),
                        opensearchpy.Q("match", **{"infT.variant": {"query": "hej", "lenient": True}}),
                    ],
                ),
            ),
        ),
        ("missing|test", opensearchpy.Q("bool", must_not=opensearchpy.Q("exists", field="test"))),
        (
            'startswith|pos|"nn"',
            get_regexp_object("pos", "nn.*"),
        ),
        ('endswith|pos|"nn"', get_regexp_object("pos", ".*nn")),
        (
            'contains|pos|"nn"',
            get_regexp_object("pos", ".*nn.*"),
        ),
        ('gt|val|"lok"', opensearchpy.Q("range", val={"gt": "lok"})),
        ("gte|val|2", opensearchpy.Q("range", val={"gte": 2})),
        ('lt|val|"lok"', opensearchpy.Q("range", val={"lt": "lok"})),
        ('lte|val|"lok"', opensearchpy.Q("range", val={"lte": "lok"})),
        ('equals|pos|"vb"', opensearchpy.Q("match_phrase", pos="vb")),
        ('regexp|kjh|"lk.*k"', get_regexp_object("kjh", "lk.*k")),
        ('not(regexp|kjh|"lk.*k")', ~get_regexp_object("kjh", "lk.*k")),
        (
            'and(regexp|baseform|"g[oe]t"||equals|pos|"nn")',
            get_regexp_object("baseform", "g[oe]t") & opensearchpy.Q("match_phrase", pos="nn"),
        ),
        (
            'and(regexp|baseform|"g[oe]t"||equals|pos|"nn"||regexp|pos|"n.*")',
            get_regexp_object("baseform", "g[oe]t")
            & opensearchpy.Q("match_phrase", pos="nn")
            & get_regexp_object("pos", "n.*"),
        ),
        (
            'or(regexp|baseform|"g[oe]t"||equals|pos|"nn")',
            get_regexp_object("baseform", "g[oe]t") | opensearchpy.Q("match_phrase", pos="nn"),
        ),
        (
            'or(regexp|baseform|"g[oe]t"||equals|pos|"nn"||regexp|pos|"n.*")',
            get_regexp_object("baseform", "g[oe]t")
            | opensearchpy.Q("match_phrase", pos="nn")
            | get_regexp_object("pos", "n.*"),
        ),
        (
            'equals|baseform|"t|est"',
            opensearchpy.Q("match_phrase", baseform="t|est"),
        ),
        (
            'equals|baseform|"|test"',
            opensearchpy.Q("match_phrase", baseform="|test"),
        ),
        (
            'equals|baseform|"test|"',
            opensearchpy.Q("match_phrase", baseform="test|"),
        ),
        (
            'and(equals|ortografi|"ständigt förknippad")',
            opensearchpy.Q("match_phrase", ortografi="ständigt förknippad"),
        ),
        (
            'and(equals|ortografi|"(ständigt) förknippad")',
            opensearchpy.Q("match_phrase", ortografi="(ständigt) förknippad"),
        ),
        (
            'and(equals|ortografi|"(ständigt förknippad")',
            opensearchpy.Q("match_phrase", ortografi="(ständigt förknippad"),
        ),
        # escaped quotes
        (
            'and(equals|baseform|"att \\"vara\\"")',
            opensearchpy.Q("match_phrase", baseform='att "vara"'),
        ),
        # no quotes work
        (
            "and(equals|baseform|noquotes)",
            opensearchpy.Q("match_phrase", baseform="noquotes"),
        ),
        (r'and(regexp|name|"\s")', get_regexp_object("name", "\\s")),
        (
            "infT(and(equals|wf|a||equals|msd|s))",
            opensearchpy.Q(
                "nested",
                path="infT",
                query=(opensearchpy.Q("match_phrase", infT__wf="a") & opensearchpy.Q("match_phrase", infT__msd="s")),
            ),
        ),
        (
            "t1(equals|infT.wf|word)",
            opensearchpy.Q(
                "nested",
                path="t1.infT",
                query=opensearchpy.Q("match_phrase", t1__infT__wf="word"),
            ),
        ),
        (
            "t1(infT(equals|wf|word))",
            opensearchpy.Q(
                "nested",
                path="t1.infT",
                query=opensearchpy.Q("match_phrase", t1__infT__wf="word"),
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
            opensearchpy.Q(
                "bool",
                must=[
                    opensearchpy.Q("exists", field="pos"),
                    opensearchpy.Q("exists", field="vb"),
                ],
            ),
        ),
        (
            "or(exists|pos||exists|vb)",
            opensearchpy.Q(
                "bool",
                should=[
                    opensearchpy.Q("exists", field="pos"),
                    opensearchpy.Q("exists", field="vb"),
                ],
            ),
        ),
        (
            "and(not(exists|pos)||not(exists|vb))",
            opensearchpy.Q(
                "bool",
                must_not=[
                    opensearchpy.Q("exists", field="pos"),
                    opensearchpy.Q("exists", field="vb"),
                ],
            ),
        ),
        (
            'not(equals|ordklass|"substantiv"||equals|ordklass|"verb")',
            opensearchpy.Q(
                "bool",
                must_not=[
                    opensearchpy.Q("match_phrase", ordklass="substantiv"),
                    opensearchpy.Q("match_phrase", ordklass="verb"),
                ],
            ),
        ),
    ],
)
def test_combined_es_query(parser, q, expected):  # noqa: ANN201
    query = es_query_builder().walk(parser.parse(q))

    assert query == expected
