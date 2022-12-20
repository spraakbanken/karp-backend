from itertools import zip_longest

import pytest  # pyre-ignore

from karp.search.domain.query_dsl import op, parser


def _test_nodes(r, facit):
    for x, f in zip_longest(r.gen_stream(), facit):
        assert x is not None, "x is too short"
        assert f is not None, "x is too long"

        assert x.type == f[0]
        assert x.value == f[1]
        assert isinstance(x.value, type(f[1]))


@pytest.mark.parametrize(
    "query,facit",
    [
        (
            "and||missing|pos||equals|wf||or|blomma|äpple",
            [
                (op.AND, None),
                (op.MISSING, None),
                (op.STRING, "pos"),
                (op.EQUALS, None),
                (op.STRING, "wf"),
                (op.ARG_OR, None),
                (op.STRING, "blomma"),
                (op.STRING, "äpple"),
            ],
        ),
        ("freetext|stort hus", [(op.FREETEXT, None), (op.STRING, "stort hus")]),
        (
            "freetext||not|stort hus",
            [(op.FREETEXT, None), (op.ARG_NOT, None), (op.STRING, "stort hus")],
        ),
        ("freetext|flicka", [(op.FREETEXT, None), (op.STRING, "flicka")]),
        (
            "freetext||and|3|flicka",
            [
                (op.FREETEXT, None),
                (op.ARG_AND, None),
                (op.INT, 3),
                (op.STRING, "flicka"),
            ],
        ),
        (
            "freetext||or|3|flicka",
            [
                (op.FREETEXT, None),
                (op.ARG_OR, None),
                (op.INT, 3),
                (op.STRING, "flicka"),
            ],
        ),
        ("freetext|6", [(op.FREETEXT, None), (op.INT, 6)]),
        (
            "startswith|lemgram|dalinm--",
            [(op.STARTSWITH, None), (op.STRING, "lemgram"), (op.STRING, "dalinm--")],
        ),
        (
            "startswith|lemgram||or|3|dalinm--",
            [
                (op.STARTSWITH, None),
                (op.STRING, "lemgram"),
                (op.ARG_OR, None),
                (op.STRING, "3"),
                (op.STRING, "dalinm--"),
            ],
        ),
        (
            "and||equals|wf|äta||missing|pos",
            [
                (op.AND, None),
                (op.EQUALS, None),
                (op.STRING, "wf"),
                (op.STRING, "äta"),
                (op.MISSING, None),
                (op.STRING, "pos"),
            ],
        ),
        (
            "regexp|wf|.*o.*a",
            [(op.REGEXP, None), (op.STRING, "wf"), (op.STRING, ".*o.*a")],
        ),
        ("exists|sense", [(op.EXISTS, None), (op.STRING, "sense")]),
        ("not||exists|sense", [("NOT", None), (op.EXISTS, None), (op.STRING, "sense")]),
        (
            "and||equals|wf|sitta||not||equals|wf|satt",
            [
                (op.AND, None),
                (op.EQUALS, None),
                (op.STRING, "wf"),
                (op.STRING, "sitta"),
                (op.NOT, None),
                (op.EQUALS, None),
                (op.STRING, "wf"),
                (op.STRING, "satt"),
            ],
        ),
        ("freergxp|str.*ng", [(op.FREERGXP, None), (op.STRING, "str.*ng")]),
        (
            "freergxp||or|str.*ng1|str.*ng2",
            [
                (op.FREERGXP, None),
                (op.ARG_OR, None),
                (op.STRING, "str.*ng1"),
                (op.STRING, "str.*ng2"),
            ],
        ),
        (
            "regexp|field||or|str.*ng1|str.*ng2",
            [
                (op.REGEXP, None),
                (op.STRING, "field"),
                (op.ARG_OR, None),
                (op.STRING, "str.*ng1"),
                (op.STRING, "str.*ng2"),
            ],
        ),
        (
            "regexp||or|field1|field2||str.*ng",
            [
                (op.REGEXP, None),
                (op.ARG_OR, None),
                (op.STRING, "field1"),
                (op.STRING, "field2"),
                (op.STRING, "str.*ng"),
            ],
        ),
        (
            "exists||or|and|or",
            [
                (op.EXISTS, None),
                (op.ARG_OR, None),
                (op.STRING, "and"),
                (op.STRING, "or"),
            ],
        ),
        ("missing|field", [(op.MISSING, None), (op.STRING, "field")]),
        ("missing|3", [(op.MISSING, None), (op.STRING, "3")]),
        (
            "equals|field|string",
            [(op.EQUALS, None), (op.STRING, "field"), (op.STRING, "string")],
        ),
        (
            "equals|field|6.7",
            [(op.EQUALS, None), (op.STRING, "field"), (op.FLOAT, 6.7)],
        ),
        (
            "and||freergxp|str.*ng||regexp|field|str.*ng",
            [
                (op.AND, None),
                (op.FREERGXP, None),
                (op.STRING, "str.*ng"),
                (op.REGEXP, None),
                (op.STRING, "field"),
                (op.STRING, "str.*ng"),
            ],
        ),
        (
            "and||freergxp|str.*ng||regexp|field|str.*ng||exists|pos",
            [
                (op.AND, None),
                (op.FREERGXP, None),
                (op.STRING, "str.*ng"),
                (op.REGEXP, None),
                (op.STRING, "field"),
                (op.STRING, "str.*ng"),
                (op.EXISTS, None),
                (op.STRING, "pos"),
            ],
        ),
        (
            "or||freergxp|str.*ng||regexp|field|str.*ng",
            [
                (op.OR, None),
                (op.FREERGXP, None),
                (op.STRING, "str.*ng"),
                (op.REGEXP, None),
                (op.STRING, "field"),
                (op.STRING, "str.*ng"),
            ],
        ),
        (
            "and||regexp||or|wordform|baseform||s.tt.?||exists|pos",
            [
                (op.AND, None),
                (op.REGEXP, None),
                (op.ARG_OR, None),
                (op.STRING, "wordform"),
                (op.STRING, "baseform"),
                (op.STRING, "s.tt.?"),
                (op.EXISTS, None),
                (op.STRING, "pos"),
            ],
        ),
        (
            "equals|field||or|string1|string2|string3",
            [
                (op.EQUALS, None),
                (op.STRING, "field"),
                (op.ARG_OR, None),
                (op.STRING, "string1"),
                (op.STRING, "string2"),
                (op.STRING, "string3"),
            ],
        ),
        (
            "contains|field|string",
            [(op.CONTAINS, None), (op.STRING, "field"), (op.STRING, "string")],
        ),
        (
            "endswith|field|string",
            [(op.ENDSWITH, None), (op.STRING, "field"), (op.STRING, "string")],
        ),
        (
            "endswith|field|56",
            [(op.ENDSWITH, None), (op.STRING, "field"), (op.STRING, "56")],
        ),
        #   ('#(child)|lt|2',[('ROOT', None),]),
        #   ('lt|#(child)|2',[('ROOT', None),]),
        ("lt|field|1", [(op.LT, None), (op.STRING, "field"), (op.INT, 1)]),
        ("lte|field|2", [(op.LTE, None), (op.STRING, "field"), (op.INT, 2)]),
        ("gt|field|3.0", [(op.GT, None), (op.STRING, "field"), (op.FLOAT, 3.0)]),
        ("gt|field|hej", [(op.GT, None), (op.STRING, "field"), (op.STRING, "hej")]),
        ("gte|field|3.14", [(op.GTE, None), (op.STRING, "field"), (op.FLOAT, 3.14)]),
        #    ('range|field|3.14|4.16',[
        #        ('ROOT', None),
        #    ]),
        (
            "or||exists|field||missing|field||and||equals|wf|bov",
            [
                (op.OR, None),
                (op.EXISTS, None),
                (op.STRING, "field"),
                (op.MISSING, None),
                (op.STRING, "field"),
                (op.AND, None),
                (op.EQUALS, None),
                (op.STRING, "wf"),
                (op.STRING, "bov"),
            ],
        ),
        (
            "exists||or|field1|field2|field3",
            [
                (op.EXISTS, None),
                (op.ARG_OR, None),
                (op.STRING, "field1"),
                (op.STRING, "field2"),
                (op.STRING, "field3"),
            ],
        ),
        (
            "and||exists|field||and||or||missing|field||contains|field|string||not||contains|field|string",
            [
                (op.AND, None),
                (op.EXISTS, None),
                (op.STRING, "field"),
                (op.AND, None),
                (op.OR, None),
                (op.MISSING, None),
                (op.STRING, "field"),
                (op.CONTAINS, None),
                (op.STRING, "field"),
                (op.STRING, "string"),
                (op.NOT, None),
                (op.CONTAINS, None),
                (op.STRING, "field"),
                (op.STRING, "string"),
            ],
        ),
        (
            "and||not||equals|wf|satt||or||exists|wf||contains|wf|sitta",
            [
                (op.AND, None),
                (op.NOT, None),
                (op.EQUALS, None),
                (op.STRING, "wf"),
                (op.STRING, "satt"),
                (op.OR, None),
                (op.EXISTS, None),
                (op.STRING, "wf"),
                (op.CONTAINS, None),
                (op.STRING, "wf"),
                (op.STRING, "sitta"),
            ],
        ),
        (
            "not||and||equals|wf|satt||or||exists|wf||contains|wf|sitta",
            [
                (op.NOT, None),
                (op.AND, None),
                (op.EQUALS, None),
                (op.STRING, "wf"),
                (op.STRING, "satt"),
                (op.OR, None),
                (op.EXISTS, None),
                (op.STRING, "wf"),
                (op.CONTAINS, None),
                (op.STRING, "wf"),
                (op.STRING, "sitta"),
            ],
        ),
        (
            "contains|name||or|vi|bo",
            [
                (op.CONTAINS, None),
                (op.STRING, "name"),
                (op.ARG_OR, None),
                (op.STRING, "vi"),
                (op.STRING, "bo"),
            ],
        ),
        (
            "contains|name||or|vi|bo",
            [
                (op.CONTAINS, None),
                (op.STRING, "name"),
                (op.ARG_OR, None),
                (op.STRING, "vi"),
                (op.STRING, "bo"),
            ],
        ),
        pytest.param(
            "equals||and|area||or|population|density||6312",
            [
                (op.EQUALS, None),
                (op.ARG_AND, None),
                (op.STRING, "area"),
                (op.ARG_OR, None),
                (op.STRING, "population"),
                (op.STRING, "density"),
                (op.INT, 6312),
            ],
            marks=pytest.mark.xfail(
                reason="Current query-dsl syntax can't handle this"
            ),
        ),
    ],
)
def test_karp_tng_parser_success(query, facit):
    r = parser.parse(query)

    assert r is not None
    r.pprint()
    _test_nodes(r, facit)
