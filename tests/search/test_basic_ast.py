import pytest

from karp.search.basic_ast import *


def test_AstNode():
    node = AstNode('test')
    assert node.num_children() == 0
    assert not node.can_add_child()
    with pytest.raises(TooManyChildren):
        node.add_child(AstNode('child'))
    with pytest.raises(StopIteration):
        gen = node.children()
        next(gen)
    assert node.num_children() == sum(1 for i in node.children())


def test_NodeWithOneChild():
    node = NodeWithOneChild('one', None)
    assert sum(1 for i in node.children()) == 0
    assert node.can_add_child()
    assert not node.has_child0()

    node.add_child(AstNode('child0'))

    assert sum(1 for i in node.children()) == 1
    assert not node.can_add_child()
    assert node.has_child0()


def test_NodeWithTwoChildren():
    node = NodeWithTwoChildren('two', None, None)
    assert sum(1 for i in node.children()) == 0
    assert node.can_add_child()
    assert not node.has_child0()
    assert not node.has_child1()

    node.add_child(AstNode('child0'))

    assert sum(1 for i in node.children()) == 1
    assert node.can_add_child()
    assert node.has_child0()
    assert not node.has_child1()

    node.add_child(AstNode('child1'))

    assert sum(1 for i in node.children()) == 2
    assert not node.can_add_child()
    assert node.has_child0()
    assert node.has_child1()


def test_NodeWithThreeChildren():
    node = NodeWithThreeChildren('three', None, None, None)
    assert sum(1 for i in node.children()) == 0
    assert node.can_add_child()
    assert not node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(AstNode('child0'))

    assert sum(1 for i in node.children()) == 1
    assert node.can_add_child()
    assert node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(AstNode('child1'))

    assert sum(1 for i in node.children()) == 2
    assert node.can_add_child()
    assert node.has_child0()
    assert node.has_child1()
    assert not node.has_child2()

    node.add_child(AstNode('child2'))

    assert sum(1 for i in node.children()) == 3
    assert not node.can_add_child()
    assert node.has_child0()
    assert node.has_child1()
    assert node.has_child2()


def test_UnaryOp_1():
    node = UnaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()

    node.add_child(AstNode('child'))

    assert not node.can_add_child()
    with pytest.raises(TooManyChildren):
        node.add_child(AstNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()


def test_UnaryOp_2():
    node = UnaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()

    node.child0 = AstNode('child')

    assert not node.can_add_child()
    with pytest.raises(TooManyChildren):
        node.add_child(AstNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()


def test_BinaryOp_1():
    node = BinaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()

    node.add_child(AstNode('child1'))

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()

    node.add_child(AstNode('child2'))

    assert node.num_children() == 2
    assert not node.can_add_child()
    with pytest.raises(TooManyChildren):
        node.add_child(AstNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()


def test_BinaryOp_2():
    node = BinaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()

    node.child0 = AstNode('child1')

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()

    node.add_child(AstNode('child2'))

    assert not node.can_add_child()
    with pytest.raises(TooManyChildren):
        node.add_child(AstNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()


def test_BinaryOp_3():
    node = BinaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()

    node.add_child(AstNode('child1'))

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()

    node.child1 = AstNode('child2')

    assert not node.can_add_child()
    with pytest.raises(TooManyChildren):
        node.add_child(AstNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()


def test_BinaryOp_4():
    node = BinaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()

    node.child0 = AstNode('child1')

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()

    node.child1 = AstNode('child2')

    assert not node.can_add_child()
    with pytest.raises(TooManyChildren):
        node.add_child(AstNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()


def test_TernaryOp_1():
    node = TernaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(AstNode('child1'))

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(AstNode('child2'))

    assert node.num_children() == 2
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert not node.has_child2()

    node.add_child(AstNode('child3'))

    assert node.num_children() == 3
    assert not node.can_add_child()
    with pytest.raises(TooManyChildren):
        node.add_child(AstNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert node.has_child2()


def test_TernaryOp_2():
    node = TernaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.child0 = AstNode('child1')

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(AstNode('child2'))

    assert node.num_children() == 2
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert not node.has_child2()

    node.add_child(AstNode('child3'))

    assert node.num_children() == 3
    assert not node.can_add_child()
    with pytest.raises(TooManyChildren):
        node.add_child(AstNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert node.has_child2()


def test_TernaryOp_3():
    node = TernaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(AstNode('child1'))

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.child1 = AstNode('child2')

    assert node.num_children() == 2
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert not node.has_child2()

    node.add_child(AstNode('child3'))

    assert node.num_children() == 3
    assert not node.can_add_child()
    with pytest.raises(TooManyChildren):
        node.add_child(AstNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert node.has_child2()


def test_TernaryOp_4():
    node = TernaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(AstNode('child1'))

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(AstNode('child2'))

    assert node.num_children() == 2
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert not node.has_child2()

    node.child2 = AstNode('child3')

    assert node.num_children() == 3
    assert not node.can_add_child()
    with pytest.raises(TooManyChildren):
        node.add_child(AstNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert node.has_child2()
