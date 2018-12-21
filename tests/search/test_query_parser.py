from karp.search import query_parser
from karp.search import basic_ast as ast


def do_test_ast_node(x, facit):
    assert isinstance(x, type(facit))
    assert x.num_children() == facit.num_children()
    for i in range(x.num_children()):
        do_test_ast_node(x.children[i], facit.children[i])


def do_test_ast(x, facit):
    assert isinstance(x, ast.Ast)
    do_test_ast_node(x.root, facit)


def test_freetext_1():
    query = query_parser.parse('freetext|test')
    do_test_ast(query,
                ast.UnaryOpNode(
                    'FREETEXT',
                    ast.StringNode('test')))

def test_freetext_2():
    query = query_parser.parse('freetext|stort hus')
    do_test_ast(query,
                ast.UnaryOpNode(
                    'FREETEXT',
                    ast.StringNode('stort hus')))

def test_regexp_1():
    query = query_parser.parse('regexp|str.*ng')
    do_test_ast(query,
                ast.BinaryOpNode(
                    'REGEXP',
                    ast.StringNode('str.*ng')))


def test_regexp_2():
    query = query_parser.parse('regexp|field|str.*ng')
    do_test_ast(query,
                ast.BinaryOpNode(
                    'REGEXP',
                    ast.StringNode('field'),
                    ast.StringNode('str.*ng')))


def test_regexp_3():
    query = query_parser.parse('regexp||str.*ng1||or||str.*ng2||')
    do_test_ast(query,
                ast.BinaryOpNode(
                    'REGEXP',
                    ast.BinLogOpNode('OR',
                                     ast.StringNode('str.*ng1'),
                                     ast.StringNode('str.*ng2'))))


def test_regexp_4():
    query = query_parser.parse('regexp|field||str.*ng1||or||str.*ng2||')
    do_test_ast(query,
                ast.BinaryOpNode(
                    'REGEXP',
                    ast.StringNode('field'),
                    ast.BinLogOpNode('OR',
                                     ast.StringNode('str.*ng1'),
                                     ast.StringNode('str.*ng2'))

                ))

def test_regexp_5():
    query = query_parser.parse('regexp||field1||or||field2||str.*ng')
    do_test_ast(query,
                ast.BinaryOpNode(
                    'REGEXP',
                    ast.BinLogOpNode('OR',
                                     ast.StringNode('field1'),
                                     ast.StringNode('field2')),
                    ast.StringNode('str.*ng')

                ))
def test_exists_1():
    query = query_parser.parse('exists|field')
    do_test_ast(query,
                ast.UnaryOpNode(
                    'EXISTS',
                    ast.StringNode('field')
                ))

examples = [
    'missing|field',
    'equals|field|string',
    'equals|field||string1||or||string2||',
    'contains|field|string',
    'startswith|field|string',
    'endswith|field|string',
    'lt|field|1',
    'lte|field|2',
    'gt|field|3.0',
    'gte|field|3.14',
    'range|field|3.14|4.16',
    '||regexp|str.*ng||and||regexp|field|str.*ng||',
    '||exists|field||or||missing|field||',
    'exists||field1||or||field2||or||field3||',
    # 'and||exists|field||and||or||missing|field||contains|field|string||not||contains|field|string',
    '||exists|field||and||missing|field||or||contains|field|string||and||not||contains|field|string||',
    '||equals|wf|sitta||and||not||equals|wf|satt||',
    '||equals|wf|äta||and||missing|pos||',
    '||not||equals|wf|satt||and||exists|wf||or||contains|wf|sitta||'
]
