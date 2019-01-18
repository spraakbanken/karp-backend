from typing import Iterable, Tuple
from . import errors


class Node:
    min_arity = 0
    max_arity = 0

    def __init__(self, value=None):
        self.value = value

    def __repr__(self) -> str:
        return "<{}>".format(self._format_self())

    def num_children(self) -> int:
        return sum(1 for i in self.children())

    def can_add_child(self) -> bool:
        return False

    def add_child(self, child) -> None:
        raise errors.TooManyChildren("Can't add a child to this node")

    def has_child(self, child) -> bool:
        return False

    def update_child(self, old_child, new_child) -> None:
        raise errors.NoChild("Can't update a child since this has no child.")

    def children(self) -> Iterable:
        if False:
            yield Node('INVALID')

    def pprint(self, level: int) -> None:
        print('-'*level, self._format_self())
        self._pprint_children(level+1)
        # print(' '*level, '>')

    def _format_self(self) -> str:
        return 'Node value={}'.format(self.value)

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
class Leaf(Node):
    def __init__(self, value):
        super().__init__(value)


class NodeWithOneChild(Node):
    def __init__(self, value, child0: Node):
        super().__init__(value)
        self.child0 = child0

    def has_child0(self) -> bool:
        return self.child0 is not None

    def children(self) -> Iterable[Node]:
        if self.has_child0():
            yield self.child0

    def can_add_child(self) -> bool:
        return not self.has_child0()

    def add_child(self, child: Node) -> None:
        if not self.has_child0():
            self.child0 = child
        else:
            raise errors.TooManyChildren('This node has a child.')

    def has_child(self, child) -> bool:
        return self.child0 is child

    def update_child(self, old_child, new_child):
        if self.child0 is old_child:
            self.child0 = new_child
        else:
            raise errors.ChildNotFound("No such child '{}'".format(old_child))

    def __repr__(self) -> str:
        return '<{} child={}>'.format(self._format_self(), repr(self.child0))


class NodeWithTwoChildren(NodeWithOneChild):
    def __init__(self, value, child0: Node, child1: Node):
        super().__init__(value, child0)
        self.child1 = child1

    def has_child1(self) -> bool:
        return self.child1 is not None

    def children(self) -> Iterable[Node]:
        yield from super().children()

        if self.has_child1():
            yield self.child1

    def can_add_child(self) -> bool:
        return super().can_add_child() or not self.has_child1()

    def add_child(self, child: Node) -> None:
        if not self.has_child0():
            self.child0 = child
        elif not self.has_child1():
            self.child1 = child
        else:
            raise errors.TooManyChildren('This node has two children.')

    def has_child(self, child) -> bool:
        return super().has_child(child) or self.child1 is child

    def update_child(self, old_child, new_child):
        if self.child0 is old_child:
            self.child0 = new_child
        elif self.child1 is old_child:
            self.child1 = new_child
        else:
            raise errors.ChildNotFound("No such child '{}'".format(old_child))

    def __repr__(self) -> str:
        return '<{} child0={} child1={}>'.format(self._format_self(), repr(self.child0), repr(self.child1))


class NodeWithThreeChildren(NodeWithTwoChildren):
    def __init__(self, value, child0: Node, child1: Node, child2: Node):
        super().__init__(value, child0, child1)
        self.child2 = child2

    def has_child2(self) -> bool:
        return self.child2 is not None

    def children(self) -> Iterable[Node]:
        yield from super().children()

        if self.has_child2():
            yield self.child2

    def can_add_child(self) -> bool:
        return super().can_add_child() or not self.has_child2()

    def add_child(self, child: Node) -> None:
        if not self.has_child0():
            self.child0 = child
        elif not self.has_child1():
            self.child1 = child
        elif not self.has_child2():
            self.child2 = child
        else:
            raise errors.TooManyChildren('This node has three children.')

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
            raise errors.ChildNotFound("No such child '{}'".format(old_child))

    def __repr__(self) -> str:
        return '<{} child0={} child1={} child2={}>'.format(self._format_self(),
                                                           repr(self.child0),
                                                           repr(self.child1),
                                                           repr(self.child2))


class Tree:
    def __init__(self, root: Node = None):
        self.root = root

    def __repr__(self):
        return "<Tree root={}>".format(repr(self.root))

    def is_empty(self) -> bool:
        return self.root is None

    def pprint(self):
        print('<Tree root=')
        if not self.is_empty():
            self.root.pprint(1)
        print('>')

    def validate_arity(self) -> Tuple[bool, str]:
        if self.is_empty():
            return True, "This tree is empty."

        result = []
        self.root.validate_arity(result)
        if not result:
            return True, None
        else:
            return False, ', '.join(result)
