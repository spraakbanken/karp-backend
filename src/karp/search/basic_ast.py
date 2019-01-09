from typing import Tuple, Iterable


class AstException(Exception):
    def __init__(self, message):
        self.message = message

    def __repr__(self):
        return "AstException message='{}'".format(self.message)


class TooManyChildren(AstException):
    def __init__(self, message):
        super().__init__(message)


# Base class
class AstNode:
    value = None
    children = None
    min_arity = 0
    max_arity = 0

    def __init__(self, value = None):
        self.value = value

    def __repr__(self) -> str:
        return "<{}>".format(self._format_self())

    def num_children(self) -> int:
        return sum(1 for i in self.children())

    def can_add_child(self) -> bool:
        return False

    def add_child(self, child) -> None:
        raise TooManyChildren("Can't add a child to this node")

    def children(self) -> Iterable:
        if False:
            yield AstNode('INVALID')

    def pprint(self, level: int) -> None:
        print('-'*level, self._format_self())
        self._pprint_children(level+1)
        # print(' '*level, '>')

    def _format_self(self) -> str:
        return 'AstNode value={}'.format(self.value)

    def _pprint_children(self, level: int) -> None:
        for child in self.children():
            child.pprint(level)

    def validate_arity(self, result):
        if self.num_children() < self.min_arity:
            result.append('Too few arguments to {}'.format(self._format_self()))
        if self.num_children() > self.max_arity:
            result.append('Too many arguments to {}'.format(self._format_self()))
        if not self.children:
            return

        for child in self.children():
            child.validate_arity(result)

    def __eq__(self, other) -> bool:
        if isinstance(self, type(other)):
            return self.__dict__ == other.__dict__
        else:
            return NotImplemented

# Mixin classes
class Leaf(AstNode):
    def __init__(self, value):
        super().__init__(value)


class InfixOp(AstNode):

    def __init__(self, value):
        super().__init__(value)

    def _format_self(self):
        return 'InfixOp'


class NodeWithOneChild(AstNode):
    def __init__(self, value, child0: AstNode):
        super().__init__(value)
        self.child0 = child0

    def has_child0(self) -> bool:
        return self.child0 != None

    def children(self) -> Iterable[AstNode]:
        if self.has_child0():
            yield self.child0

    def can_add_child(self) -> bool:
        return not self.has_child0()

    def add_child(self, child: AstNode) -> None:
        if not self.has_child0():
            self.child0 = child
        else:
            raise TooManyChildren('This node has a child.')


class NodeWithTwoChildren(NodeWithOneChild):
    def __init__(self, value, child0: AstNode, child1: AstNode):
        super().__init__(value, child0)
        self.child1 = child1

    def has_child1(self) -> bool:
        return self.child1 != None

    def children(self) -> Iterable[AstNode]:
        yield from super().children()

        if self.has_child1():
            yield self.child1

    def can_add_child(self) -> bool:
        return super().can_add_child() or not self.has_child1()

    def add_child(self, child: AstNode) -> None:
        if not self.has_child0():
            self.child0 = child
        elif not self.has_child1():
            self.child1 = child
        else:
            raise TooManyChildren('This node has two children.')


class NodeWithThreeChildren(NodeWithTwoChildren):
    def __init__(self, value, child0: AstNode, child1: AstNode, child2: AstNode):
        super().__init__(value, child0, child1)
        self.child2 = child2

    def has_child2(self) -> bool:
        return self.child2 != None

    def children(self) -> Iterable[AstNode]:
        yield from super().children()

        if self.has_child2():
            yield self.child2

    def can_add_child(self) -> bool:
        return super().can_add_child() or not self.has_child2()

    def add_child(self, child: AstNode) -> None:
        if not self.has_child0():
            self.child0 = child
        elif not self.has_child1():
            self.child1 = child
        elif not self.has_child2():
            self.child2 = child
        else:
            raise TooManyChildren('This node has three children.')


# Real classes
class UnaryOp(NodeWithOneChild):

    def __init__(self, value, child0=None, min_arity=1):
        super().__init__(value, child0)
        self.min_arity = min_arity
        self.max_arity = 2

    def __repr__(self):
        return "<{} child={}>".format(self._format_self(),
                                     repr(self.child0))

    def _format_self(self):
        return 'UnaryOp op={}'.format(self.value)


class BinaryOp(NodeWithTwoChildren):

    def __init__(self, op, child0=None, child1=None, min_arity=2):
        super().__init__(op, child0, child1)
        self.min_arity = min_arity
        self.max_arity = 3

    def __repr__(self):
        return "{} left={} right={}>".format(self._format_self(),
                                             repr(self.child0),
                                             repr(self.child1))

    def _format_self(self):
        return 'BinaryOp op={}'.format(self.value)



class TernaryOp(NodeWithThreeChildren):

    def __init__(self, op, child0=None, child1=None, child2=None, min_arity=3):
        super().__init__(op, child0, child1, child2)
        self.min_arity = min_arity
        self.max_arity = 4

    def __repr__(self):
        return "{} child0={} child1={} child2={}>".format(self._format_self(),
                                             repr(self.child0),
                                             repr(self.child1),
                                             repr(self.child2))

    def _format_self(self):
        return '<TernaryOpNode op={}'.format(self.op)


# class InfixOp(AstNode):
#
#     def __init__(self, op, min_arity, max_arity):
#         super().__init__(op, min_arity, max_arity)
#
#     def _format_self(self):
#         return 'InfixOp op={}'.format(self.value)


class UnaryInfixOp(UnaryOp, InfixOp):

    def __init__(self, op, child=None):
        super().__init__(value=op, child0=child)

    def _format_self(self):
        return 'UnaryInfixOp op={}'.format(self.value)


class BinaryInfixOp(BinaryOp, InfixOp):

    def __init__(self, op, child0=None, child1=None):
        super().__init__(op, child0, child1)
    #     self.add_child(left)
    #     self.add_child(right)
    #
    # def has_left(self) -> bool:
    #     return self.num_children() > 0
    #
    # @property
    # def left(self):
    #     return self.children[0]
    #
    # @left.setter
    # def left(self, child):
    #     self.children[0] = child
    #
    # def has_right(self) -> bool:
    #     return self.num_children() > 1
    #
    # @property
    # def right(self):
    #     return self.children[1]
    #
    # @right.setter
    # def right(self, child):
    #     self.children[1] = child
    #
    # def __repr__(self):
    #     return "{} left={} right={}>".format(self._format_self(),
    #                                          repr(self.left),
    #                                          repr(self.right))

    def _format_self(self):
        return 'BinaryInfixOp op={}'.format(self.value)


class ArgNode(AstNode):

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


def binary_infix_operator(op_name):
    def result():
        return BinaryInfixOp(op_name)
    return result


def unary_infix_operator(op_name):
    def result():
        return UnaryInfixOp(op_name)
    return result


def logical_operator(op_name, min_arity, max_arity):
    def result():
        return InfixOp(op_name, min_arity, max_arity)
    return result


def query_operator(op_name, min_arity, max_arity):
    def result():
        return OpNode(op_name, min_arity, max_arity)
    return result


def ternary_query_operator(op_name):
    def result():
        return TernaryOp(op_name)
    return result


def binary_query_operator(op_name, **kwargs):
    def result():
        return BinaryOp(op_name, **kwargs)
    return result


def unary_query_operator(op_name):
    def result():
        return UnaryOp(op_name)
    return result


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


class Ast:
    def __init__(self, root: AstNode = None):
        assert isinstance(root, AstNode), "Wrong type"
        self.root = root if root else AstNode()

    def __repr__(self):
        return "<Ast root={}>".format(repr(self.root))

    def pprint(self):
        print('<Ast root=')
        self.root.pprint(1)

    def validate_arity(self) -> Tuple[bool, str]:
        result = []
        self.root.validate_arity(result)
        if not result:
            return True, None
        else:
            return False, ', '.join(result)
