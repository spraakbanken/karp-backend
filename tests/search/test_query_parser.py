import pytest

from karp.search import basic_ast as ast
from karp.search import query_parser


@pytest.fixture
def parser():
    return query_parser.QueryParser()


def do_test_ast_node(x, facit):
    assert isinstance(x, type(facit))
    assert x.value == facit.value
    assert x.num_children() == facit.num_children()
    for x_child, facit_child in zip(x.children(), facit.children()):
        do_test_ast_node(x_child, facit_child)


def do_test_ast(x, facit):
    assert isinstance(x, ast.Ast)
    do_test_ast_node(x.root, facit)


def test_ParseError():
    e = query_parser.ParseError('test')
    assert repr(e) == "ParseError message='test'"


def test_SyntaxError():
    e = query_parser.SyntaxError('test')
    assert isinstance(e, query_parser.ParseError)
    assert repr(e) == "SyntaxError message='test'"


def test_missing_and_equals_karp_v5_query_language(parser):
    # extended||and|pos|missing||and||wf|equals|blomma|äpple
    query = parser.parse('and||missing|pos||equals|wf||or|blomma|äpple')
    do_test_ast(query,
                ast.BinaryOp(
                    query_parser.Operator.AND,
                    ast.UnaryOp(
                        query_parser.Operator.MISSING,
                        ast.StringNode('pos')
                    ),
                    ast.BinaryOp(
                        query_parser.Operator.EQUALS,
                        ast.StringNode('wf'),
                        ast.BinaryOp(
                            query_parser.Operator.OR,
                            ast.StringNode('blomma'),
                            ast.StringNode('äpple')
                        )
                    )
                ))


def test_freetext_karp_v5_query_1(parser):
    query = parser.parse('freetext|stort hus')
    do_test_ast(query,
                ast.UnaryOp(
                    query_parser.Operator.FREETEXT,
                    ast.StringNode('stort hus')
                ))


def test_freetext_karp_v5_simple_2(parser):
    query = parser.parse('freetext|flicka')
    do_test_ast(query,
                ast.UnaryOp(
                    query_parser.Operator.FREETEXT,
                    ast.StringNode('flicka')
                ))


def test_startswith_karp_v5_extended_1(parser):
    query = parser.parse('startswith|lemgram|dalinm--')
    do_test_ast(query,
                ast.BinaryOp(
                    query_parser.Operator.STARTSWITH,
                    ast.StringNode('lemgram'),
                    ast.StringNode('dalinm--')
                ))


def test_and_equals_missing_karp_v5_extended_2(parser):
    query = parser.parse('and||equals|wf|äta||missing|pos')
    do_test_ast(query,
                ast.BinaryOp(
                    query_parser.Operator.AND,
                    ast.BinaryOp(
                        query_parser.Operator.EQUALS,
                        ast.StringNode('wf'),
                        ast.StringNode('äta')
                    ),
                    ast.UnaryOp(
                        query_parser.Operator.MISSING,
                        ast.StringNode('pos')
                    )
                ))


def test_regexp_karp_v5_extended_3_and_4(parser):
    query = parser.parse('regexp|wf|.*o.*a')
    do_test_ast(query,
                ast.BinaryOp(
                    query_parser.Operator.REGEXP,
                    ast.StringNode('wf'),
                    ast.StringNode('.*o.*a')
                ))


def test_exists_karp_v5_extended_5(parser):
    query = parser.parse('exists|sense')
    do_test_ast(query,
                ast.UnaryOp(
                    query_parser.Operator.EXISTS,
                    ast.StringNode('sense')
                ))


def test_and_equals_not_equals_karp_v5_extended_6(parser):
    query = parser.parse('and||equals|wf|sitta||not||equals|wf|satt')
    do_test_ast(query,
                ast.BinaryOp(
                    query_parser.Operator.AND,
                    ast.BinaryOp(
                        query_parser.Operator.EQUALS,
                        ast.StringNode('wf'),
                        ast.StringNode('sitta')
                    ),
                    ast.UnaryOp(
                        query_parser.Operator.NOT,
                        ast.BinaryOp(
                            query_parser.Operator.EQUALS,
                            ast.StringNode('wf'),
                            ast.StringNode('satt')
                        )
                    )
                ))


def test_fail_no_operator(parser):
    with pytest.raises(query_parser.SyntaxError):
        parser.parse('freett|litet hus')


def test_fail_too_many_operators(parser):
    with pytest.raises(query_parser.SyntaxError):
        parser.parse('and||exists|wordform||exists|baseform||exists|pos')


def test_freergxp_1(parser):
    query = parser.parse('freergxp|str.*ng')
    do_test_ast(query,
                ast.UnaryOp(
                    query_parser.Operator.FREERGXP,
                    ast.StringNode('str.*ng')))


def test_fail_freergxp_too_many_arguments(parser):
    with pytest.raises(query_parser.ParseError):
        parser.parse('freergxp|str.*ng1|str.*ng2')


def test_freergxp_with_or(parser):
    query = parser.parse('freergxp||or|str.*ng1|str.*ng2')
    do_test_ast(query,
                ast.UnaryOp(
                    query_parser.Operator.FREERGXP,
                    ast.BinaryOp(
                        query_parser.Operator.OR,
                        ast.StringNode('str.*ng1'),
                        ast.StringNode('str.*ng2')
                    )
                ))


def test_regexp_with_or_in_2nd_arg(parser):
    query = parser.parse('regexp|field||or|str.*ng1|str.*ng2')
    do_test_ast(query,
                ast.BinaryOp(
                    query_parser.Operator.REGEXP,
                    ast.StringNode('field'),
                    ast.BinaryOp(
                        query_parser.Operator.OR,
                        ast.StringNode('str.*ng1'),
                        ast.StringNode('str.*ng2')
                    )
                ))


def test_regexp_with_or_in_1st_arg(parser):
    query = parser.parse('regexp||or|field1|field2||str.*ng')
    do_test_ast(query,
                ast.BinaryOp(
                    query_parser.Operator.REGEXP,
                    ast.BinaryOp(
                        query_parser.Operator.OR,
                        ast.StringNode('field1'),
                        ast.StringNode('field2')
                    ),
                    ast.StringNode('str.*ng')
                ))


def test_exists_with_or_and_operator_names_as_arguments(parser):
    q = parser.parse('exists||or|and|or')
    do_test_ast(q,
                ast.UnaryOp(
                    query_parser.Operator.EXISTS,
                    ast.BinaryOp(
                        query_parser.Operator.OR,
                        ast.StringNode('and'),
                        ast.StringNode('or')
                    )
                ))


def test_missing_1(parser):
    query = parser.parse('missing|field')
    do_test_ast(query,
                ast.UnaryOp(
                    query_parser.Operator.MISSING,
                    ast.StringNode('field')
                ))


def test_equals_1(parser):
    q = parser.parse('equals|field|string')
    do_test_ast(
        q,
        ast.BinaryOp(
            query_parser.Operator.EQUALS,
            ast.StringNode('field'),
            ast.StringNode('string')
        )
    )


def test_freergxp_and_regexp(parser):
    q = parser.parse('and||freergxp|str.*ng||regexp|field|str.*ng')
    do_test_ast(q,
                ast.BinaryOp(
                    query_parser.Operator.AND,
                    ast.UnaryOp(
                        query_parser.Operator.FREERGXP,
                        ast.StringNode('str.*ng')
                    ),
                    ast.BinaryOp(
                        query_parser.Operator.REGEXP,
                        ast.StringNode('field'),
                        ast.StringNode('str.*ng')
                    )
                ))


def test_exists_and_regex_with_or(parser):
    q = parser.parse('and||regexp||or|wordform|baseform||s.tt.?||exists|pos')
    do_test_ast(q,
                ast.BinaryOp(
                    query_parser.Operator.AND,
                    ast.BinaryOp(
                        query_parser.Operator.REGEXP,
                        ast.BinaryOp(
                            query_parser.Operator.OR,
                            ast.StringNode('wordform'),
                            ast.StringNode('baseform')
                        ),
                        ast.StringNode('s.tt.?')
                    ),
                    ast.UnaryOp(
                        query_parser.Operator.EXISTS,
                        ast.StringNode('pos')
                    )
                ))


def test_equals_with_or_in_2nd_arg(parser):
    query = parser.parse('equals|field||or|string1|string2')
    do_test_ast(query,
                ast.BinaryOp(
                    query_parser.Operator.EQUALS,
                    ast.StringNode('field'),
                    ast.BinaryOp(
                        query_parser.Operator.OR,
                        ast.StringNode('string1'),
                        ast.StringNode('string2')
                    )
                ))


def test_contains(parser):
    query = parser.parse('contains|field|string')
    do_test_ast(query,
                ast.BinaryOp(
                    query_parser.Operator.CONTAINS,
                    ast.StringNode('field'),
                    ast.StringNode('string')
                ))


def test_endswith(parser):
    query = parser.parse('endswith|field|string')
    do_test_ast(query,
                ast.BinaryOp(
                    query_parser.Operator.ENDSWITH,
                    ast.StringNode('field'),
                    ast.StringNode('string')
                ))


# def test_lt_function(parser):
#     query = parser.parse('#(child)|lt|2')
#     query = parser.parse('lt|#(child)|2')
#     do_test_ast(query,
#                 ast.BinaryOp(
#                     query_parser.Operator.LT,
#                     ast.StringNode('field'),
#                     ast.IntNode(1)
#                 ))


def test_lt(parser):
    query = parser.parse('lt|field|1')
    do_test_ast(query,
                ast.BinaryOp(
                    query_parser.Operator.LT,
                    ast.StringNode('field'),
                    ast.IntNode(1)
                ))


def test_lte(parser):
    query = parser.parse('lte|field|2')
    do_test_ast(query,
                ast.BinaryOp(
                    query_parser.Operator.LTE,
                    ast.StringNode('field'),
                    ast.IntNode(2)
                ))


def test_gt(parser):
    query = parser.parse('gt|field|3.0')
    do_test_ast(query,
                ast.BinaryOp(
                    query_parser.Operator.GT,
                    ast.StringNode('field'),
                    ast.FloatNode(3.0)
                ))


def test_gte(parser):
    query = parser.parse('gte|field|3.14')
    do_test_ast(query,
                ast.BinaryOp(
                    query_parser.Operator.GTE,
                    ast.StringNode('field'),
                    ast.FloatNode(3.14)
                ))


def test_range(parser):
    query = parser.parse('range|field|3.14|4.16')
    do_test_ast(query,
                ast.TernaryOp(
                    query_parser.Operator.RANGE,
                    ast.StringNode('field'),
                    ast.FloatNode(3.14),
                    ast.FloatNode(4.16)
                ))


def test_exists_or_missing(parser):
    query = parser.parse('or||exists|field||missing|field')
    do_test_ast(query,
                ast.BinaryOp(
                    query_parser.Operator.OR,
                    ast.UnaryOp(
                        query_parser.Operator.EXISTS,
                        ast.StringNode('field')
                    ),
                    ast.UnaryOp(
                        query_parser.Operator.MISSING,
                        ast.StringNode('field')
                    )
                ))


def test_exists_with_or_and_or_in_1st_arg(parser):
    query = parser.parse('exists||or||or|field1|field2||field3')
    do_test_ast(query,
                ast.UnaryOp(
                    query_parser.Operator.EXISTS,
                    ast.BinaryOp(
                        query_parser.Operator.OR,
                        ast.BinaryOp(
                            query_parser.Operator.OR,
                            ast.StringNode('field1'),
                            ast.StringNode('field2')
                        ),
                        ast.StringNode('field3')
                    )
                ))


def test_exists_with_or_and_or_in_2nd_arg(parser):
    query = parser.parse('exists||or|field1||or|field2|field3')
    do_test_ast(query,
                ast.UnaryOp(
                    query_parser.Operator.EXISTS,
                    ast.BinaryOp(
                        query_parser.Operator.OR,
                        ast.StringNode('field1'),
                        ast.BinaryOp(
                            query_parser.Operator.OR,
                            ast.StringNode('field2'),
                            ast.StringNode('field3')
                        )
                    )
                ))


def test_complex_and(parser):
    query = parser.parse('and||exists|field||and||or||missing|field||contains|field|string||not||contains|field|string')
    # query = parser.parse('||exists|field||and||missing|field||or||contains|field|string||and||not||contains|field|string||')
    do_test_ast(query,
                ast.BinaryOp(
                    query_parser.Operator.AND,
                    ast.UnaryOp(
                        query_parser.Operator.EXISTS,
                        ast.StringNode('field')
                    ),
                    ast.BinaryOp(
                        query_parser.Operator.AND,
                        ast.BinaryOp(
                            query_parser.Operator.OR,
                            ast.UnaryOp(
                                query_parser.Operator.MISSING,
                                ast.StringNode('field')
                            ),
                            ast.BinaryOp(
                                query_parser.Operator.CONTAINS,
                                ast.StringNode('field'),
                                ast.StringNode('string')
                            )
                        ),
                        ast.UnaryOp(
                            query_parser.Operator.NOT,
                            ast.BinaryOp(
                                query_parser.Operator.CONTAINS,
                                ast.StringNode('field'),
                                ast.StringNode('string')
                            )
                        )
                    )
                ))


def test_and_not(parser):
    query = parser.parse('and||not||equals|wf|satt||or||exists|wf||contains|wf|sitta')
    do_test_ast(query,
                ast.BinaryOp(
                    query_parser.Operator.AND,
                    ast.UnaryOp(
                        query_parser.Operator.NOT,
                        ast.BinaryOp(
                            query_parser.Operator.EQUALS,
                            ast.StringNode('wf'),
                            ast.StringNode('satt')
                        )
                    ),
                    ast.BinaryOp(
                        query_parser.Operator.OR,
                        ast.UnaryOp(
                            query_parser.Operator.EXISTS,
                            ast.StringNode('wf')
                        ),
                        ast.BinaryOp(
                            query_parser.Operator.CONTAINS,
                            ast.StringNode('wf'),
                            ast.StringNode('sitta')
                        )
                    )
                ))


def test_not_and(parser):
    query = parser.parse('not||and||equals|wf|satt||or||exists|wf||contains|wf|sitta')
    do_test_ast(query,
                ast.UnaryOp(
                    query_parser.Operator.NOT,
                    ast.BinaryOp(
                        query_parser.Operator.AND,
                        ast.BinaryOp(
                            query_parser.Operator.EQUALS,
                            ast.StringNode('wf'),
                            ast.StringNode('satt')
                        ),
                        ast.BinaryOp(
                            query_parser.Operator.OR,
                            ast.UnaryOp(
                                query_parser.Operator.EXISTS,
                                ast.StringNode('wf')
                            ),
                            ast.BinaryOp(
                                query_parser.Operator.CONTAINS,
                                ast.StringNode('wf'),
                                ast.StringNode('sitta')
                            )
                        )
                    )
                ))
