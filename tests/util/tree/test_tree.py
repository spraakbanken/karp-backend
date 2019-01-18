import pytest

from karp.util import tree


def test_TreeException():
    e = tree.errors.TreeException('test')
    assert repr(e) == "TreeException message='test'"


def test_Node():
    node = tree.Node('test')
    assert node.num_children() == 0
    assert not node.can_add_child()
    with pytest.raises(tree.errors.TooManyChildren):
        node.add_child(tree.Node('child'))
    with pytest.raises(StopIteration):
        gen = node.children()
        next(gen)
    assert node.num_children() == sum(1 for i in node.children())


def test_NodeWithOneChild():
    node = tree.NodeWithOneChild('one', None)
    assert sum(1 for i in node.children()) == 0
    assert node.can_add_child()
    assert not node.has_child0()

    node.add_child(tree.Node('child0'))

    assert sum(1 for i in node.children()) == 1
    assert not node.can_add_child()
    assert node.has_child0()


def test_NodeWithTwoChildren():
    node = tree.NodeWithTwoChildren('two', None, None)
    assert sum(1 for i in node.children()) == 0
    assert node.can_add_child()
    assert not node.has_child0()
    assert not node.has_child1()

    node.add_child(tree.Node('child0'))

    assert sum(1 for i in node.children()) == 1
    assert node.can_add_child()
    assert node.has_child0()
    assert not node.has_child1()

    node.add_child(tree.Node('child1'))

    assert sum(1 for i in node.children()) == 2
    assert not node.can_add_child()
    assert node.has_child0()
    assert node.has_child1()


def test_NodeWithThreeChildren():
    node = tree.NodeWithThreeChildren('three', None, None, None)
    assert sum(1 for i in node.children()) == 0
    assert node.can_add_child()
    assert not node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(tree.Node('child0'))

    assert sum(1 for i in node.children()) == 1
    assert node.can_add_child()
    assert node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(tree.Node('child1'))

    assert sum(1 for i in node.children()) == 2
    assert node.can_add_child()
    assert node.has_child0()
    assert node.has_child1()
    assert not node.has_child2()

    node.add_child(tree.Node('child2'))

    assert sum(1 for i in node.children()) == 3
    assert not node.can_add_child()
    assert node.has_child0()
    assert node.has_child1()
    assert node.has_child2()
