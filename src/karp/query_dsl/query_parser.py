import collections

from . import basic_ast as ast
from . import errors


class Operators:
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
    'and': ast.binary_operator(Operators.AND),
    'or': ast.binary_operator(Operators.OR),
    'not': ast.unary_operator(Operators.NOT),
    'freetext': ast.unary_operator(Operators.FREETEXT),
    'freergxp': ast.unary_operator(Operators.FREERGXP),
    'regexp': ast.binary_operator(Operators.REGEXP),
    'exists': ast.unary_operator(Operators.EXISTS),
    'missing': ast.unary_operator(Operators.MISSING),
    'equals': ast.binary_operator(Operators.EQUALS),
    'contains': ast.binary_operator(Operators.CONTAINS),
    'startswith': ast.binary_operator(Operators.STARTSWITH),
    'endswith': ast.binary_operator(Operators.ENDSWITH),
    'lt': ast.binary_operator(Operators.LT),
    'lte': ast.binary_operator(Operators.LTE),
    'gt': ast.binary_operator(Operators.GT),
    'gte': ast.binary_operator(Operators.GTE),
    'range': ast.ternary_operator(Operators.RANGE),
}


class QueryParser():
    def create_node(self, s: str) -> ast.tree.Node:
        node_creator = OPERATORS.get(s)
        if not node_creator:
            try:
                int_value = int(s)
                return ast.IntNode(int_value)
            except ValueError:
                pass

            try:
                float_value = float(s)
                return ast.FloatNode(float_value)
            except ValueError:
                pass

            return ast.StringNode(s)

        return node_creator()

    def _sub_expr(self, s):
        exprs = s.split('|')

        _node = self.create_node(exprs[0])

        if not isinstance(_node, ast.ArgNode):
            for expr in exprs[1:]:
                if _node.can_add_child():
                    _node.add_child(self.create_node(expr))
                else:
                    raise errors.SyntaxError("Too many arguments to '{}'".format(_node))
        elif len(exprs) > 1:
            raise errors.SyntaxError("Can't add '{}' to '{}'. Did you miss a '|'?".format(exprs[1:], _node))

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
                        raise errors.ParseError('Too complex query')
                else:
                    raise errors.ParseError('Too complex query')
            else:
                raise errors.SyntaxError("Too many operators. Can't combine '{}' and '{}'".format(curr, node))

        while len(node_stack) > 0:
            parent = node_stack.pop()

            while not parent.can_add_child():
                new_parent = node_stack.pop()

                if new_parent.can_add_child():
                    new_parent.add_child(parent)
                else:
                    raise errors.ParseError('Too complex query.')
                parent = new_parent
            parent.add_child(curr)
            curr = parent

        q = collections.deque()
        q.append(_node)
        while len(q) > 0:
            curr = q.popleft()
            for child in curr.children():
                if child.min_arity > 0 and child.num_children() == 0:
                    new_child = ast.StringNode(child.value.lower())
                    curr.update_child(child, new_child)
                else:
                    q.append(child)

        return _node

    def parse(self, s: str) -> ast.Ast:
        # print('parsing "{}"'.format(s))
        root_node = self._expr(s)
        try:
            _ast = ast.Ast(root_node)
        except ast.tree.errors.TreeException as e:
            raise errors.ParseError(e.msg)
        except errors.ParseError as e:
            raise e
        ok, error = _ast.validate_arity()
        if ok:
            return _ast
        else:
            raise errors.ParseError(error)


_parser = QueryParser()


def parse(s: str) -> ast.Ast:
    if not s:
        return ast.Ast(None)

    return _parser.parse(s)
