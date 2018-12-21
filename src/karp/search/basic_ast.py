from typing import Tuple


class AstNode:
    children = None

    def __init__(self, min_arity: int = 0, max_arity: int = 20):
        self.min_arity = min_arity
        self.max_arity = max_arity
        if self.max_arity > self.min_arity:
            self.children = []

    def __repr__(self) -> str:
        return "{} children={}>".format(self._format_self(), repr(self.children))

    def num_children(self) -> int:
        return len(self.children) if self.children else 0

    def add_child(self, child):
        assert self.num_children() < self.max_arity
        self.children.append(child)

    def pprint(self, level: int):
        print('-'*level, self._format_self())
        self._pprint_children(level+1)
        # print(' '*level, '>')

    def _format_self(self) -> str:
        return '<AstNode'

    def _pprint_children(self, level: int):
        if self.children:
            for child in self.children:
                child.pprint(level)

    def validate_arity(self, result):
        if self.num_children() < self.min_arity:
            result.append('Too few arguments to {}'.format(repr(self)))
        if self.num_children() > self.max_arity:
            result.append('Too many arguments to {}'.format(repr(self)))
        if not self.children:
            return

        for child in self.children:
            child.validate_arity(result)

class OpNode(AstNode):
    op = None

    def __init__(self, op, min_arity, max_arity):
        super().__init__(min_arity, max_arity)
        self.op = op

    def _format_self(self):
        return '<OpNode op={}'.format(self.op)

class UnaryOpNode(OpNode):

    def __init__(self, op, child=None):
        super().__init__(op, min_arity=1, max_arity=2)
        if child:
            self.add_child(child)

    def has_child(self) -> bool:
        return self.num_children() > 0

    @property
    def child(self):
        return self.children[0]

    @child.setter
    def child(self, child):
        if self.has_child():
            self.children[0] = child
        else:
            self.add_child(child)

    def __repr__(self):
        return "{} child={}>".format(self._format_self(),
                                     repr(self.child))

    def _format_self(self):
        return '<UnaryOpNode op={}'.format(self.op)


class BinaryOpNode(OpNode):

    def __init__(self, op, left=None, right=None, min_arity=2):
        super().__init__(op=op, min_arity=min_arity, max_arity=3)
        if left:
            self.add_child(left)
        if right:
            self.add_child(right)

    def has_left(self) -> bool:
        return self.num_children() > 0

    @property
    def left(self):
        return self.children[0]

    @left.setter
    def left(self, child):
        if self.has_left():
            self.children[0] = child
        else:
            self.add_child(child)

    def has_right(self) -> bool:
        return self.num_children() > 1

    @property
    def right(self):
        return self.children[1]

    @right.setter
    def right(self, child):
        if self.has_right():
            self.children[1] = child
        else:
            if not self.has_left():
                self.add_child(None)
            self.add_child(child)

    def __repr__(self):
        return "{} left={} right={}>".format(self._format_self(),
                                             repr(self.left),
                                             repr(self.right))

    def _format_self(self):
        return '<BinaryOpNode op={}'.format(self.op)


class TernaryOpNode(OpNode):

    def __init__(self, op, first=None, second=None, third=None):
        super().__init__(op, min_arity=3, max_arity=4)
        if first:
            self.add_child(first)
        if second:
            self.add_child(second)
        if third:
            self.add_child(third)

    def has_first(self) -> bool:
        return self.num_children() > 0

    @property
    def first(self):
        return self.children[0]

    @first.setter
    def first(self, child):
        if self.has_first():
            self.children[0] = child
        else:
            self.add_child(child)

    def has_second(self) -> bool:
        return self.num_children() > 1

    @property
    def second(self):
        return self.children[1]

    @second.setter
    def second(self, child):
        if self.has_second():
            self.children[1] = child
        else:
            if not self.has_first():
                self.add_child(None)
            self.add_child(child)

    def has_third(self) -> bool:
        return self.num_children() > 2

    @property
    def third(self):
        return self.children[2]

    @third.setter
    def third(self, child):
        if self.has_third():
            self.children[2] = child
        else:
            if not self.has_first():
                self.add_child(None)
            if not self.has_second():
                self.add_child(None)
            self.add_child(child)

    def __repr__(self):
        return "{} first={} second={} third={}>".format(self._format_self(),
                                             repr(self.first),
                                             repr(self.second),
                                             repr(self.third))

    def _format_self(self):
        return '<TernaryOpNode op={}'.format(self.op)


class LogOpNode(OpNode):

    def __init__(self, op, min_arity, max_arity):
        super().__init__(op, min_arity, max_arity)

    def _format_self(self):
        return '<LogOpNode op={}'.format(self.op)


class UnaryLogOpNode(UnaryOpNode, LogOpNode):

    def __init__(self, op, child=None):
        super().__init__(op=op, min_arity=1, max_arity=2, child=child)

    def _format_self(self):
        return '<UnaryLogOpNode op={}'.format(self.op)


class BinLogOpNode(BinaryOpNode, LogOpNode):

    def __init__(self, op, left=None, right=None):
        super().__init__(op, left=left, right=right)
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
        return '<BinLogOpNode op={}'.format(self.op)


class ArgNode(AstNode):

    def __init__(self, arg):
        super().__init__(min_arity=0, max_arity=0)
        self.arg = arg

    def __repr__(self):
        return "<ArgNode arg={}>".format(self.arg)

    _format_self = __repr__


class StringNode(ArgNode):

    def __init__(self, arg: str):
        assert isinstance(arg, str), "Wrong type"
        super().__init__(arg)

    def __repr__(self):
        return "<StringNode str={}>".format(self.arg)

    _format_self = __repr__


class IntNode(ArgNode):

    def __init__(self, arg: int):
        assert isinstance(arg, int), "Wrong type"
        super().__init__(arg)

    def __repr__(self):
        return "<IntNode value={}>".format(self.arg)

    _format_self = __repr__


class FloatNode(ArgNode):

    def __init__(self, arg: float):
        assert isinstance(arg, float), "Wrong type"
        super().__init__(arg)

    def __repr__(self):
        return "<FloatNode value={}>".format(self.arg)

    _format_self = __repr__


def binary_logical_operator(op_name):
    def result():
        return BinLogOpNode(op_name)
    return result


def unary_logical_operator(op_name):
    def result():
        return UnaryLogOpNode(op_name)
    return result


def logical_operator(op_name, min_arity, max_arity):
    def result():
        return LogOpNode(op_name, min_arity, max_arity)
    return result


def query_operator(op_name, min_arity, max_arity):
    def result():
        return OpNode(op_name, min_arity, max_arity)
    return result


def ternary_query_operator(op_name):
    def result():
        return TernaryOpNode(op_name)
    return result


def binary_query_operator(op_name, **kwargs):
    def result():
        return BinaryOpNode(op_name, **kwargs)
    return result


def unary_query_operator(op_name):
    def result():
        return UnaryOpNode(op_name)
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
