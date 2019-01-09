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


def test_freetext_1(parser):
    query = parser.parse('freetext|test')
    do_test_ast(query,
                ast.UnaryOp(
                    'FREETEXT',
                    ast.StringNode('test')))

def test_freetext_2(parser):
    query = parser.parse('freetext|stort hus')
    do_test_ast(query,
                ast.UnaryOp(
                    'FREETEXT',
                    ast.StringNode('stort hus')))

def test_regexp_1(parser):
    query = parser.parse('regexp|str.*ng')
    do_test_ast(query,
                ast.BinaryOp(
                    'REGEXP',
                    ast.StringNode('str.*ng')))


def test_regexp_2(qp):
    query = qp.parse('regexp|field|str.*ng')
    do_test_ast(query,
                ast.BinaryOp(
                    'REGEXP',
                    ast.StringNode('field'),
                    ast.StringNode('str.*ng')))


def test_regexp_3(parser):
    query = parser.parse('regexp||or|str.*ng1|str.*ng2')
    do_test_ast(query,
                ast.BinaryOp(
                    'REGEXP',
                    ast.BinaryOp('OR',
                                     ast.StringNode('str.*ng1'),
                                     ast.StringNode('str.*ng2'))))


def test_regexp_4(parser):
    query = parser.parse('regexp|field||or|str.*ng1|str.*ng2')
    do_test_ast(query,
                ast.BinaryOp(
                    'REGEXP',
                    ast.StringNode('field'),
                    ast.BinaryOp('OR',
                                     ast.StringNode('str.*ng1'),
                                     ast.StringNode('str.*ng2'))

                ))

def test_regexp_5(parser):
    query = parser.parse('regexp||or|field1|field2||str.*ng')
    do_test_ast(query,
                ast.BinaryOp(
                    'REGEXP',
                    ast.BinaryOp('OR',
                                     ast.StringNode('field1'),
                                     ast.StringNode('field2')),
                    ast.StringNode('str.*ng')

                ))

def test_or_1(parser):
    q = parser.parse('exists||or|and|or')
    do_test_ast(q,
                ast.UnaryOp(
                    'EXISTS',
                    ast.BinaryOp('OR',
                                   ast.StringNode('and'),
                                   ast.StringNode('or'))
                ))


def test_exists_1(parser):
    query = parser.parse('exists|field')
    do_test_ast(query,
                ast.UnaryOp(
                    'EXISTS',
                    ast.StringNode('field')
                ))

def test_missing_1(parser):
    query = parser.parse('missing|field')
    do_test_ast(query,
                ast.UnaryOp(
                    'MISSING',
                    ast.StringNode('field')
                ))

def test_equals_1(parser):
    q = parser.parse('equals|field|string')
    do_test_ast(
        q,
        ast.BinaryOp(
            'EQUALS',
            ast.StringNode('field'),
            ast.StringNode('string')
        )
    )


def test_and_1(parser):
    q = parser.parse('and||regexp|str.*ng||regexp|field|str.*ng')
    do_test_ast(q,
                ast.BinaryOp(
                    'AND',
                    ast.BinaryOp(
                        'REGEXP',
                        ast.StringNode('str.*ng')
                    ),
                    ast.BinaryOp(
                        'REGEXP',
                        ast.StringNode('field'),
                        ast.StringNode('str.*ng')
                    )
                ))


def test_equals_with_or(parser):
    query = parser.parse('equals|field||or|string1|string2')
    do_test_ast(query,
                ast.BinaryOp(
                    'EQUALS',
                    ast.StringNode('field'),
                    ast.BinaryOp(
                        'OR',
                        ast.StringNode('string1'),
                        ast.StringNode('string2')
                    )
                ))


def test_contains(parser):
    query = parser.parse('contains|field|string')
    do_test_ast(query,
                ast.BinaryOp(
                    'CONTAINS',
                    ast.StringNode('field'),
                    ast.StringNode('string')
                ))


def test_startswith(parser):
    query = parser.parse('startswith|field|string')
    do_test_ast(query,
                ast.BinaryOp(
                    'STARTSWITH',
                    ast.StringNode('field'),
                    ast.StringNode('string')
                ))


def test_endswith(parser):
    query = parser.parse('endswith|field|string')
    do_test_ast(query,
                ast.BinaryOp(
                    'ENDSWITH',
                    ast.StringNode('field'),
                    ast.StringNode('string')
                ))


def test_lt_function(parser):
    query = parser.parse('#(child)|lt|2')
    query = parser.parse('lt|#(child)|2')
    do_test_ast(query,
                ast.BinaryOp(
                    'LT',
                    ast.StringNode('field'),
                    ast.IntNode(1)
                ))


def test_lt(parser):
    query = parser.parse('lt|field|1')
    do_test_ast(query,
                ast.BinaryOp(
                    'LT',
                    ast.StringNode('field'),
                    ast.IntNode(1)
                ))


def test_lte(parser):
    query = parser.parse('lte|field|2')
    do_test_ast(query,
                ast.BinaryOp(
                    'LTE',
                    ast.StringNode('field'),
                    ast.IntNode(2)
                ))


def test_gt(parser):
    query = parser.parse('gt|field|3.0')
    do_test_ast(query,
                ast.BinaryOp(
                    'GT',
                    ast.StringNode('field'),
                    ast.FloatNode(3.0)
                ))


def test_gte(parser):
    query = parser.parse('gte|field|3.14')
    do_test_ast(query,
                ast.BinaryOp(
                    'GTE',
                    ast.StringNode('field'),
                    ast.FloatNode(3.14)
                ))


def test_range(parser):
    query = parser.parse('range|field|3.14|4.16')
    do_test_ast(query,
                ast.TernaryOp(
                    'RANGE',
                    ast.StringNode('field'),
                    ast.FloatNode(3.14),
                    ast.FloatNode(4.16)
                ))


def test_or_exists_missing(parser):
    query = parser.parse('or||exists|field||missing|field')
    do_test_ast(query,
                ast.BinaryOp(
                    'OR',
                    ast.UnaryOp(
                        'EXISTS',
                        ast.StringNode('field')
                    ),
                    ast.UnaryOp(
                        'MISSING',
                        ast.StringNode('field')
                    )
                ))


def test_exists_with_or(parser):
    query = parser.parse('exists||or|field1||or|field2|field3')
    do_test_ast(query,
                ast.UnaryOp(
                    'EXISTS',
                    ast.BinaryOp(
                        'OR',
                        ast.StringNode('field1'),
                        ast.BinaryOp(
                            'OR',
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
                    'AND',
                    ast.UnaryOp(
                        'EXISTS',
                        ast.StringNode('field')
                    ),
                    ast.BinaryOp(
                        'AND',
                        ast.BinaryOp(
                            'OR',
                            ast.UnaryOp(
                                'MISSING',
                                ast.StringNode('field')
                            ),
                            ast.BinaryOp(
                                'CONTAINS',
                                ast.StringNode('field'),
                                ast.StringNode('string')
                            )
                        ),
                        ast.UnaryOp(
                            'NOT',
                            ast.BinaryOp(
                                'CONTAINS',
                                ast.StringNode('field'),
                                ast.StringNode('string')
                            )
                        )
                    )
                ))


def test_and_equals_not_equals(parser):
    query = parser.parse('and||equals|wf|sitta||not||equals|wf|satt')
    do_test_ast(query,
                ast.BinaryOp(
                    'AND',
                    ast.BinaryOp(
                        'EQUALS',
                        ast.StringNode('wf'),
                        ast.StringNode('sitta')
                    ),
                    ast.UnaryOp(
                        'NOT',
                        ast.BinaryOp(
                            'EQUALS',
                            ast.StringNode('wf'),
                            ast.StringNode('satt')
                        )
                    )
                ))


def test_and_equals_missing(parser):
    query = parser.parse('and||equals|wf|äta||missing|pos')
    do_test_ast(query,
                ast.BinaryOp(
                    'AND',
                    ast.BinaryOp(
                        'EQUALS',
                        ast.StringNode('wf'),
                        ast.StringNode('äta')
                    ),
                    ast.UnaryOp(
                        'MISSING',
                        ast.StringNode('pos')
                    )
                ))


def test_and_not(parser):
    query = parser.parse('and||not||equals|wf|satt||or||exists|wf||contains|wf|sitta')
    do_test_ast(query,
                ast.BinaryOp(
                    'AND',
                    ast.UnaryOp(
                        'NOT',
                        ast.BinaryOp(
                            'EQUALS',
                            ast.StringNode('wf'),
                            ast.StringNode('satt')
                        )
                    ),
                    ast.BinaryOp(
                        'OR',
                        ast.UnaryOp(
                            'EXISTS',
                            ast.StringNode('wf')
                        ),
                        ast.BinaryOp(
                            'CONTAINS',
                            ast.StringNode('wf'),
                            ast.StringNode('sitta')
                        )
                    )
                ))



def test_not_and(parser):
    query = parser.parse('not||and||equals|wf|satt||or||exists|wf||contains|wf|sitta')
    do_test_ast(query,
                ast.UnaryOp(
                    'NOT',
                    ast.BinaryOp(
                        'AND',
                        ast.BinaryOp(
                            'EQUALS',
                            ast.StringNode('wf'),
                            ast.StringNode('satt')
                        ),
                        ast.BinaryOp(
                            'OR',
                            ast.UnaryOp(
                                'EXISTS',
                                ast.StringNode('wf')
                            ),
                            ast.BinaryOp(
                                'CONTAINS',
                                ast.StringNode('wf'),
                                ast.StringNode('sitta')
                            )
                        )
                    )
                ))
