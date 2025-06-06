import pytest  # noqa: I001

import elasticsearch_dsl as es_dsl

from karp.search.domain.query_dsl.karp_query_parser import KarpQueryParser
from karp.search.domain.query_dsl.karp_query_model import KarpQueryModelBuilderSemantics
from karp.search.infrastructure.es import EsQueryBuilder
from karp.search.infrastructure.es.mapping_repo import Field


@pytest.fixture(scope="session")
def parser() -> KarpQueryParser:
    return KarpQueryParser(semantics=KarpQueryModelBuilderSemantics())


class MappingRepo:
    """
    For these query parser tests, infT means that the field is nested, no matter
    where in the hierachy it appears
    """

    def __init__(self):
        pass

    def get_fields_as_tree(self, _, __):
        return {
            "infT": {
                "def": Field(path=["infT"], type="nested"),
                "children": {
                    "field1": {"def": Field(path=["infT.field1"], type="text"), "children": {}},
                    "field2": {"def": Field(path=["infT.field1"], type="boolean"), "children": {}},
                },
            }
        }

    def is_nested(self, _, field):
        return field.endswith("infT")

    def get_field(self, _, field_name):
        return Field(path=[field_name], type="text")


def es_query_builder():
    mapping_repo = MappingRepo()
    return EsQueryBuilder("r", mapping_repo)


def get_regexp_object(field, val):
    return es_dsl.Q(
        "query_string",
        query=f"/{val}/",
        fields=[field],
        lenient=True,
    )


@pytest.mark.parametrize(
    "q,expected",
    [
        ("exists|test", es_dsl.Q("exists", field="test")),
        (
            'freetext|"hej"',
            es_dsl.Q(
                "nested",
                path="infT",
                query=es_dsl.Q(
                    "bool",
                    should=[
                        es_dsl.Q("match_phrase", **{"infT.field1": "hej"}),
                        es_dsl.Q("match", **{"infT.field2": {"query": "hej", "lenient": True}}),
                    ],
                ),
            ),
        ),
        ("missing|test", es_dsl.Q("bool", must_not=es_dsl.Q("exists", field="test"))),
        (
            'startswith|pos|"nn"',
            get_regexp_object("pos", "nn.*"),
        ),
        ('endswith|pos|"nn"', get_regexp_object("pos", ".*nn")),
        (
            'contains|pos|"nn"',
            get_regexp_object("pos", ".*nn.*"),
        ),
        ('gt|val|"lok"', es_dsl.Q("range", val={"gt": "lok"})),
        ("gte|val|2", es_dsl.Q("range", val={"gte": 2})),
        ('lt|val|"lok"', es_dsl.Q("range", val={"lt": "lok"})),
        ('lte|val|"lok"', es_dsl.Q("range", val={"lte": "lok"})),
        ('equals|pos|"vb"', es_dsl.Q("match_phrase", pos="vb")),
        ('regexp|kjh|"lk.*k"', get_regexp_object("kjh", "lk.*k")),
        ('not(regexp|kjh|"lk.*k")', ~get_regexp_object("kjh", "lk.*k")),
        (
            'and(regexp|baseform|"g[oe]t"||equals|pos|"nn")',
            get_regexp_object("baseform", "g[oe]t") & es_dsl.Q("match_phrase", pos="nn"),
        ),
        (
            'and(regexp|baseform|"g[oe]t"||equals|pos|"nn"||regexp|pos|"n.*")',
            get_regexp_object("baseform", "g[oe]t")
            & es_dsl.Q("match_phrase", pos="nn")
            & get_regexp_object("pos", "n.*"),
        ),
        (
            'or(regexp|baseform|"g[oe]t"||equals|pos|"nn")',
            get_regexp_object("baseform", "g[oe]t") | es_dsl.Q("match_phrase", pos="nn"),
        ),
        (
            'or(regexp|baseform|"g[oe]t"||equals|pos|"nn"||regexp|pos|"n.*")',
            get_regexp_object("baseform", "g[oe]t")
            | es_dsl.Q("match_phrase", pos="nn")
            | get_regexp_object("pos", "n.*"),
        ),
        (
            'equals|baseform|"t|est"',
            es_dsl.Q("match_phrase", baseform="t|est"),
        ),
        (
            'equals|baseform|"|test"',
            es_dsl.Q("match_phrase", baseform="|test"),
        ),
        (
            'equals|baseform|"test|"',
            es_dsl.Q("match_phrase", baseform="test|"),
        ),
        (
            'and(equals|ortografi|"ständigt förknippad")',
            es_dsl.Q("match_phrase", ortografi="ständigt förknippad"),
        ),
        (
            'and(equals|ortografi|"(ständigt) förknippad")',
            es_dsl.Q("match_phrase", ortografi="(ständigt) förknippad"),
        ),
        (
            'and(equals|ortografi|"(ständigt förknippad")',
            es_dsl.Q("match_phrase", ortografi="(ständigt förknippad"),
        ),
        # escaped quotes
        (
            'and(equals|baseform|"att \\"vara\\"")',
            es_dsl.Q("match_phrase", baseform='att "vara"'),
        ),
        # no quotes work
        (
            "and(equals|baseform|noquotes)",
            es_dsl.Q("match_phrase", baseform="noquotes"),
        ),
        (r'and(regexp|name|"\s")', get_regexp_object("name", "\\s")),
        (
            "infT(and(equals|wf|a||equals|msd|s))",
            es_dsl.Q(
                "nested",
                path="infT",
                query=(es_dsl.Q("match_phrase", infT__wf="a") & es_dsl.Q("match_phrase", infT__msd="s")),
            ),
        ),
        (
            "t1(equals|infT.wf|word)",
            es_dsl.Q(
                "nested",
                path="t1.infT",
                query=es_dsl.Q("match_phrase", t1__infT__wf="word"),
            ),
        ),
        (
            "t1(infT(equals|wf|word))",
            es_dsl.Q(
                "nested",
                path="t1.infT",
                query=es_dsl.Q("match_phrase", t1__infT__wf="word"),
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
                    es_dsl.Q("match_phrase", ordklass="substantiv"),
                    es_dsl.Q("match_phrase", ordklass="verb"),
                ],
            ),
        ),
    ],
)
def test_combined_es_query(parser, q, expected):  # noqa: ANN201
    query = es_query_builder().walk(parser.parse(q))

    assert query == expected
