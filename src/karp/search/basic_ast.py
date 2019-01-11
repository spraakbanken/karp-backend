from typing import Tuple, Iterable


class AstException(Exception):
    def __init__(self, message):
        self.message = message

    def __repr__(self):
        return "AstException message='{}'".format(self.message)


class TooManyChildren(AstException):
    def __init__(self, message):
        super().__init__(message)


class NoChild(AstException):
    def __init__(self, message):
        super().__init__(message)


class ChildNotFound(AstException):
    def __init__(self, message):
        super().__init__(message)


# Base class
class AstNode:
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

    def has_child(self, child) -> bool:
        return False

    def update_child(self, old_child, new_child) -> None:
        raise NoChild("Can't update a child since this has no child.")

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

    def has_child(self, child) -> bool:
        return self.child0 is child

    def update_child(self, old_child, new_child):
        if self.child0 is old_child:
            self.child0 = new_child
        else:
            raise ChildNotFound("No such child '{}'".format(old_child))

    def __repr__(self) -> str:
        return '<{} child={}>'.format(self._format_self(), repr(self.child0))


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

    def has_child(self, child) -> bool:
        return super().has_child(child) or self.child1 is child

    def update_child(self, old_child, new_child):
        if self.child0 is old_child:
            self.child0 = new_child
        elif self.child1 is old_child:
            self.child1 = new_child
        else:
            raise ChildNotFound("No such child '{}'".format(old_child))

    def __repr__(self) -> str:
        return '<{} child0={} child1={}>'.format(self._format_self(), repr(self.child0), repr(self.child1))


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

    def has_child(self, child) -> bool:
        return super().has_child(child) or self.child2 is child

    def update_child(self, old_child, new_child):
        if self.child0 is old_child:
            self.child0 = new_child
        elif self.child1 is old_child:
            self.child1 = new_child
        elif self.child2 is old_child:
            self.child2 = new_child
        else:
            raise ChildNotFound("No such child '{}'".format(old_child))

    def __repr__(self) -> str:
        return '<{} child0={} child1={} child2={}>'.format(self._format_self(), repr(self.child0), repr(self.child1), repr(self.child2))

# Real classes
class UnaryOp(NodeWithOneChild):

    def __init__(self, value, child0=None, min_arity=1):
        super().__init__(value, child0)
        self.min_arity = min_arity
        self.max_arity = 2

    def _format_self(self):
        return 'UnaryOp op={}'.format(self.value)


class BinaryOp(NodeWithTwoChildren):

    def __init__(self, op, child0=None, child1=None, min_arity=2):
        super().__init__(op, child0, child1)
        self.min_arity = min_arity
        self.max_arity = 3

    def _format_self(self):
        return 'BinaryOp op={}'.format(self.value)



class TernaryOp(NodeWithThreeChildren):

    def __init__(self, op, child0=None, child1=None, child2=None, min_arity=3):
        super().__init__(op, child0, child1, child2)
        self.min_arity = min_arity
        self.max_arity = 4

    def _format_self(self):
        return '<TernaryOpNode op={}'.format(self.op)


class ArgNode(Leaf):

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
