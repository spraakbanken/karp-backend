from typing import Tuple, Iterable

from karp.util import tree


class UnaryOp(tree.NodeWithOneChild):

    def __init__(self, value, child0=None, min_arity=1):
        super().__init__(value, child0)
        self.min_arity = min_arity
        self.max_arity = 2

    def _format_self(self):
        return 'UnaryOp op={}'.format(self.value)


class BinaryOp(tree.NodeWithTwoChildren):

    def __init__(self, op, child0=None, child1=None, min_arity=2):
        super().__init__(op, child0, child1)
        self.min_arity = min_arity
        self.max_arity = 3

    def _format_self(self):
        return 'BinaryOp op={}'.format(self.value)


class TernaryOp(tree.NodeWithThreeChildren):

    def __init__(self, op, child0=None, child1=None, child2=None, min_arity=3):
        super().__init__(op, child0, child1, child2)
        self.min_arity = min_arity
        self.max_arity = 4

    def _format_self(self):
        return '<TernaryOpNode op={}'.format(self.op)


class ArgNode(tree.Node):

    def __init__(self, arg):
        super().__init__(value=arg)

    def __repr__(self):
        return "<ArgNode arg={}>".format(self.value)

    _format_self = __repr__


class StringNode(ArgNode):

    def __init__(self, arg: str):
        assert isinstance(arg, str), "Wrong type"
        super().__init__(arg)

    def __repr__(self):
        return "<StringNode str={}>".format(self.value)

    _format_self = __repr__


class IntNode(ArgNode):

    def __init__(self, arg: int):
        assert isinstance(arg, int), "Wrong type"
        super().__init__(arg)

    def __repr__(self):
        return "<IntNode value={}>".format(self.value)

    _format_self = __repr__


class FloatNode(ArgNode):

    def __init__(self, arg: float):
        assert isinstance(arg, float), "Wrong type"
        super().__init__(arg)

    def __repr__(self):
        return "<FloatNode value={}>".format(self.value)

    _format_self = __repr__


def ternary_operator(op_name):
    def result():
        return TernaryOp(op_name)
    return result


def binary_operator(op_name, **kwargs):
    def result():
        return BinaryOp(op_name, **kwargs)
    return result


def unary_operator(op_name):
    def result():
        return UnaryOp(op_name)
    return result


class Ast(tree.Tree):
    pass
