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


class OpNode(AstNode):
    op = None

    def __init__(self, op, min_arity, max_arity):
        super().__init__(min_arity, max_arity)
        self.op = op

    def _format_self(self):
        return '<OpNode op={}'.format(self.op)

class LogOpNode(OpNode):

    def __init__(self, op, min_arity, max_arity):
        super().__init__(op, min_arity, max_arity)

    def _format_self(self):
        return '<LogOpNode op={}'.format(self.op)


class BinLogOpNode(LogOpNode):

    def __init__(self, op, left=None, right=None):
        super().__init__(op, min_arity=2, max_arity=3)
        self.add_child(left)
        self.add_child(right)

    def has_left(self) -> bool:
        return self.num_children() > 0

    @property
    def left(self):
        return self.children[0]

    @left.setter
    def left(self, child):
        self.children[0] = child

    def has_right(self) -> bool:
        return self.num_children() > 1

    @property
    def right(self):
        return self.children[1]

    @right.setter
    def right(self, child):
        self.children[1] = child

    def __repr__(self):
        return "{} left={} right={}>".format(self._format_self(),
                                             repr(self.left),
                                             repr(self.right))

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


def logical_operator(op_name, min_arity, max_arity):
    def result():
        return LogOpNode(op_name, min_arity, max_arity)
    return result


def query_operator(op_name, min_arity, max_arity):
    def result():
        return OpNode(op_name, min_arity, max_arity)
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
