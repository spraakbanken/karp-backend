from typing import List
import queue

from .basic_ast import *
# from .parser import Parser




class ParseError(BaseException):
    def __init__(self, msg: str) -> None:
        self.msg = msg


class SyntaxError(ParseError):
    def __init__(self, msg: str):
        super().__init__(msg)


class Operator():
    AND = 'AND'
    OR = 'OR'
    NOT = 'NOT'
    FREETEXT = 'FREETEXT'
    FREERGXP = 'FREERGXP'
    REGEXP = 'REGEXP'
    EXISTS = 'EXISTS'
    MISSING = 'MISSING'
    EQUALS = 'EQUALS'
    CONTAINS = 'CONTAINS'
    STARTSWITH = 'STARTSWITH'
    ENDSWITH = 'ENDSWITH'
    LT = 'LT'
    LTE = 'LTE'
    GT = 'GT'
    GTE = 'GTE'
    RANGE = 'RANGE'

OPERATORS = {
    'and': binary_operator(Operator.AND),
    'or': binary_operator(Operator.OR),
    'not': unary_operator(Operator.NOT),
    'freetext': unary_operator(Operator.FREETEXT),
    'freergxp': unary_operator(Operator.FREERGXP),
    'regexp': binary_operator(Operator.REGEXP),
    'exists': unary_operator(Operator.EXISTS),
    'missing': unary_operator(Operator.MISSING),
    'equals': binary_operator(Operator.EQUALS),
    'contains': binary_operator(Operator.CONTAINS),
    'startswith': binary_operator(Operator.STARTSWITH),
    'endswith': binary_operator(Operator.ENDSWITH),
    'lt': binary_operator(Operator.LT),
    'lte': binary_operator(Operator.LTE),
    'gt': binary_operator(Operator.GT),
    'gte': binary_operator(Operator.GTE),
    'range': ternary_operator(Operator.RANGE),
}


class QueryParser():
    def create_ast_node(self, s: str) -> AstNode:
        node_creator = OPERATORS.get(s)
        if not node_creator:
            try:
                int_value = int(s)
                return IntNode(int_value)
            except ValueError:
                pass

            try:
                float_value = float(s)
                return FloatNode(float_value)
            except ValueError:
                pass

            return StringNode(s)

        return node_creator()


    def _sub_expr(self, s):
        exprs = s.split('|')

        _node = self.create_ast_node(exprs[0])

        if not isinstance(_node, ArgNode):
            for expr in exprs[1:]:
                _node.add_child(self.create_ast_node(expr))
        elif len(exprs) > 1:
            raise SyntaxError("Can't add '{}' to '{}'. Did you miss a '|'?".format(exprs[1:], _node))

        return _node



    def _expr(self, s):
        exprs = s.split('||')

        if len(exprs) == 1:
            return self._sub_expr(s)

        _node = self._sub_expr(exprs[0])

        node_stack = []
        curr = _node
        for expr in exprs[1:]:
            node = self._sub_expr(expr)

            if node.can_add_child():
                node_stack.append(curr)
                curr = node
            elif curr.can_add_child():
                curr.add_child(node)
            elif len(node_stack) > 0:
                new_curr = node_stack.pop()
                if new_curr.can_add_child():
                    new_curr.add_child(curr)
                    if new_curr.can_add_child():
                        new_curr.add_child(node)
                        curr = new_curr
                    else:
                        raise ParseError('Too complex query')
                else:
                    raise ParseError('Too complex query')

            else:
                raise ParseError("Can't combine '{}' and '{}'".format(curr, node))

        while len(node_stack) > 0:
            parent = node_stack.pop()

            while not parent.can_add_child():
                new_parent = node_stack.pop()

                if new_parent.can_add_child():
                    new_parent.add_child(parent)
                else:
                    raise ParseError('Too complex query.')
                parent = new_parent
            parent.add_child(curr)
            curr = parent

        q = queue.SimpleQueue()
        q.put(_node)
        while not q.empty():
            curr = q.get()
            for child in curr.children():
                if child.min_arity > 0 and child.num_children() == 0:
                    new_child = StringNode(child.value.lower())
                    curr.update_child(child, new_child)
                else:
                    q.put(child)

        return _node





    def parse(self, s: str) -> Ast:
        # print('parsing "{}"'.format(s))
        root_node = self._expr(s)
        ast = Ast(root_node)
        ok, error = ast.validate_arity()
        if ok:
            return ast
        else:
            raise ParseError(error)
