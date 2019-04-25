from itertools import zip_longest

import pytest

from karp.query_dsl import karp_tng_parser as parser
from karp.query_dsl.karp_tng_parser import op


def _test_nodes(r, facit):
    for x, f in zip_longest(r.gen_stream(), facit):
        assert x is not None, 'x is too short'
        assert f is not None, 'x is too long'

        assert x.type == f[0]
        assert x.value == f[1]
        assert isinstance(x.value, type(f[1]))


@pytest.mark.parametrize('query,facit', [
    # ('and||missing|pos||equals|wf||or|blomma|äpple',[
    #    (op.AND, None),
    #    (op.MISSING, None),
    #    (op.STRING, 'pos'),
    #    (op.EQUALS, None),
    #    (op.STRING, 'wf'),
    #    (op.ARG_OR, None),
    #    (op.STRING, 'blomma'),
    #    (op.STRING, 'äpple'),
    # ]),
    ('freetext|stort hus',[
        (op.FREETEXT, None),
        (op.STRING, 'stort hus'),
    ]),
    ('freetext|flicka',[
        (op.FREETEXT, None),
        (op.STRING, 'flicka'),
    ]),
    ('freetext|6',[
        (op.FREETEXT, None),
        (op.INT, 6),
    ]),
    ('startswith|lemgram|dalinm--',[
        (op.STARTSWITH, None),
        (op.STRING, 'lemgram'),
        (op.STRING, 'dalinm--'),
    ]),
    ('and||equals|wf|äta||missing|pos',[
        (op.AND, None),
        (op.EQUALS, None),
        (op.STRING, 'wf'),
        (op.STRING, 'äta'),
        (op.MISSING, None),
        (op.STRING, 'pos'),
    ]),
    ('regexp|wf|.*o.*a',[
        (op.REGEXP, None),
        (op.STRING, 'wf'),
        (op.STRING, '.*o.*a'),
    ]),
    ('exists|sense',[
        (op.EXISTS, None),
        (op.STRING, 'sense'),
    ]),
    ('not||exists|sense',[
        ('NOT', None),
        (op.EXISTS, None),
        (op.STRING, 'sense'),
    ]),
    ('and||equals|wf|sitta||not||equals|wf|satt',[
        (op.AND, None),
        (op.EQUALS, None),
        (op.STRING, 'wf'),
        (op.STRING, 'sitta'),
        (op.NOT, None),
        (op.EQUALS, None),
        (op.STRING, 'wf'),
        (op.STRING, 'satt'),
    ]),
    ('freergxp|str.*ng',[
        (op.FREERGXP, None),
        (op.STRING, 'str.*ng'),
    ]),
#    ('freergxp||or|str.*ng1|str.*ng2',[
#        ('ROOT', None),
#    ]),
#    ('regexp|field||or|str.*ng1|str.*ng2',[
#        ('ROOT', None),
#    ]),
#    ('regexp||or|field1|field2||str.*ng',[
#        ('ROOT', None),
#    ]),
#    ('exists||or|and|or',[
#        ('ROOT', None),
#    ]),
    ('missing|field',[
        (op.MISSING, None),
        (op.STRING, 'field'),
    ]),
    ('missing|3',[
        (op.MISSING, None),
        (op.STRING, '3'),
    ]),
    ('equals|field|string',[
        (op.EQUALS, None),
        (op.STRING, 'field'),
        (op.STRING, 'string'),
    ]),
    ('equals|field|6.7',[
        (op.EQUALS, None),
        (op.STRING, 'field'),
        (op.FLOAT, 6.7),
    ]),
    ('and||freergxp|str.*ng||regexp|field|str.*ng',[
        (op.AND, None),
        (op.FREERGXP, None),
        (op.STRING, 'str.*ng'),
        (op.REGEXP, None),
        (op.STRING, 'field'),
        (op.STRING, 'str.*ng'),
    ]),
    ('and||freergxp|str.*ng||regexp|field|str.*ng||exists|pos',[
        (op.AND, None),
        (op.FREERGXP, None),
        (op.STRING, 'str.*ng'),
        (op.REGEXP, None),
        (op.STRING, 'field'),
        (op.STRING, 'str.*ng'),
        (op.EXISTS, None),
        (op.STRING, 'pos')
    ]),
    ('or||freergxp|str.*ng||regexp|field|str.*ng',[
        (op.OR, None),
        (op.FREERGXP, None),
        (op.STRING, 'str.*ng'),
        (op.REGEXP, None),
        (op.STRING, 'field'),
        (op.STRING, 'str.*ng'),
    ]),
#    ('and||regexp||or|wordform|baseform||s.tt.?||exists|pos',[
#        ('ROOT', None),
#    ]),
#    ('equals|field||or|string1|string2',[
#        ('ROOT', None),
#    ]),
    ('contains|field|string',[
        (op.CONTAINS, None),
        (op.STRING, 'field'),
        (op.STRING, 'string'),
    ]),
    ('endswith|field|string',[
        (op.ENDSWITH, None),
        (op.STRING, 'field'),
        (op.STRING, 'string'),
    ]),
    ('endswith|field|56',[
        (op.ENDSWITH, None),
        (op.STRING, 'field'),
        (op.STRING, '56'),
    ]),
#   ('#(child)|lt|2',[('ROOT', None),]),
#   ('lt|#(child)|2',[('ROOT', None),]),
    ('lt|field|1',[
        (op.LT, None),
        (op.STRING, 'field'),
        (op.INT, 1),
    ]),
    ('lte|field|2',[
        (op.LTE, None),
        (op.STRING, 'field'),
        (op.INT, 2),
    ]),
    ('gt|field|3.0',[
        (op.GT, None),
        (op.STRING, 'field'),
        (op.FLOAT, 3.0),
    ]),
    ('gt|field|hej',[
        (op.GT, None),
        (op.STRING, 'field'),
        (op.STRING, 'hej'),
    ]),
    ('gte|field|3.14',[
        (op.GTE, None),
        (op.STRING, 'field'),
        (op.FLOAT, 3.14),
    ]),
#    ('range|field|3.14|4.16',[
#        ('ROOT', None),
#    ]),
    ('or||exists|field||missing|field||and||equals|wf|bov',[
        (op.OR, None),
        (op.EXISTS, None),
        (op.STRING, 'field'),
        (op.MISSING, None),
        (op.STRING, 'field'),
        (op.AND, None),
        (op.EQUALS, None),
        (op.STRING, 'wf'),
        (op.STRING, 'bov'),
    ]),
#    ('exists||or||or|field1|field2||field3',[
#        ('ROOT', None),
#    ]),
#    ('exists||or|field1||or|field2|field3',[
#        ('ROOT', None),
#    ]),
#     ('and||exists|field||and||or||missing|field||contains|field|string||not||contains|field|string',[
#        (op.AND, None),
#        (op.EXISTS, None),
#        (op.STRING, 'field'),
#    ]),
#    	('and||not||equals|wf|satt||or||exists|wf||contains|wf|sitta',[
#        ('ROOT', None),
#    ]),
#    ('not||and||equals|wf|satt||or||exists|wf||contains|wf|sitta',[
#        ('ROOT', None),
#    ]),
])
def test_karp_tng_parser_success(query, facit):
    r = parser.parse(query)

    assert r is not None

    _test_nodes(r, facit)
