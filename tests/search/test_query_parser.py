from karp.search import query_parser
from karp.search import basic_ast as ast

def do_test_ast(x):
    assert isinstance(x, ast.Ast)


def do_test_arg_node(x, arg):
    assert isinstance(x, ast.ArgNode)
    if isinstance(arg, int):
        assert isinstance(x, ast.IntNode)
    elif isinstance(arg, float):
        assert isinstance(x, ast.FloatNode)
    else:
        assert isinstance(x, ast.StringNode)
    assert x.arg == arg

def do_test_op_node(x, op_name, args):
    do_test_ast(x)
    assert isinstance(x.root, ast.OpNode)
    assert x.root.op == op_name
    if isinstance(args, list):
        assert x.root.num_children() == len(args)
        for i, arg in enumerate(args):
            do_test_arg_node(x.root.children[i], arg)
    else:
        assert x.root.num_children() == 1
        do_test_arg_node(x.root.children[0], args)


def test_freetext_1():
    query = query_parser.parse('freetext|test')
    do_test_op_node(query, 'FREETEXT', 'test')

def test_freetext_2():
    query = query_parser.parse('freetext|stort hus')
    do_test_op_node(query, 'FREETEXT', 'stort hus')

def test_regexp_1():
    query = query_parser.parse('regexp|str.*ng')
    do_test_op_node(query, 'REGEXP', 'str.*ng')


def test_regexp_2():
    query = query_parser.parse('regexp|field|str.*ng')
    do_test_op_node(query, 'REGEXP', ['field', 'str.*ng'])


def test_regexp_3():
    query = query_parser.parse('regexp||str.*ng1||or||str.*ng2||')
examples = [
    'regexp||str.*ng1||or||str.*ng2||',
    'regexp|field||str.*ng1||or||str.*ng2||',
    'regexp||field||or||field2||str.*ng',
    'exists|field',
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
