import pytest

from karp.query_dsl import basic_ast as ast


def test_UnaryOp_1():
    node = ast.UnaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()

    node.add_child(ast.ArgNode('child'))

    assert not node.can_add_child()
    with pytest.raises(ast.tree.errors.TooManyChildren):
        node.add_child(ast.ArgNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()


def test_UnaryOp_2():
    node = ast.UnaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()

    node.child0 = ast.ArgNode('child')

    assert not node.can_add_child()
    with pytest.raises(ast.tree.errors.TooManyChildren):
        node.add_child(ast.ArgNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()


def test_BinaryOp_1():
    node = ast.BinaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()

    node.add_child(ast.ArgNode('child1'))

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()

    node.add_child(ast.ArgNode('child2'))

    assert node.num_children() == 2
    assert not node.can_add_child()
    with pytest.raises(ast.tree.errors.TooManyChildren):
        node.add_child(ast.ArgNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()


def test_BinaryOp_2():
    node = ast.BinaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()

    node.child0 = ast.ArgNode('child1')

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()

    node.add_child(ast.ArgNode('child2'))

    assert not node.can_add_child()
    with pytest.raises(ast.tree.errors.TooManyChildren):
        node.add_child(ast.ArgNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()


def test_BinaryOp_3():
    node = ast.BinaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()

    node.add_child(ast.ArgNode('child1'))

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()

    node.child1 = ast.ArgNode('child2')

    assert not node.can_add_child()
    with pytest.raises(ast.tree.errors.TooManyChildren):
        node.add_child(ast.ArgNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()


def test_BinaryOp_4():
    node = ast.BinaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()

    node.child0 = ast.ArgNode('child1')

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()

    node.child1 = ast.ArgNode('child2')

    assert not node.can_add_child()
    with pytest.raises(ast.tree.errors.TooManyChildren):
        node.add_child(ast.ArgNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()


def test_TernaryOp_1():
    node = ast.TernaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(ast.ArgNode('child1'))

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(ast.ArgNode('child2'))

    assert node.num_children() == 2
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert not node.has_child2()

    node.add_child(ast.ArgNode('child3'))

    assert node.num_children() == 3
    assert not node.can_add_child()
    with pytest.raises(ast.tree.errors.TooManyChildren):
        node.add_child(ast.ArgNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert node.has_child2()


def test_TernaryOp_2():
    node = ast.TernaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.child0 = ast.ArgNode('child1')

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(ast.ArgNode('child2'))

    assert node.num_children() == 2
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert not node.has_child2()

    node.add_child(ast.ArgNode('child3'))

    assert node.num_children() == 3
    assert not node.can_add_child()
    with pytest.raises(ast.tree.errors.TooManyChildren):
        node.add_child(ast.ArgNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert node.has_child2()


def test_TernaryOp_3():
    node = ast.TernaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(ast.ArgNode('child1'))

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.child1 = ast.ArgNode('child2')

    assert node.num_children() == 2
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert not node.has_child2()

    node.add_child(ast.ArgNode('child3'))

    assert node.num_children() == 3
    assert not node.can_add_child()
    with pytest.raises(ast.tree.errors.TooManyChildren):
        node.add_child(ast.ArgNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert node.has_child2()


def test_TernaryOp_4():
    node = ast.TernaryOp('test')

    assert node.num_children() == 0
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert not node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(ast.ArgNode('child1'))

    assert node.num_children() == 1
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert not node.has_child1()
    assert not node.has_child2()

    node.add_child(ast.ArgNode('child2'))

    assert node.num_children() == 2
    assert node.can_add_child()
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert not node.has_child2()

    node.child2 = ast.ArgNode('child3')

    assert node.num_children() == 3
    assert not node.can_add_child()
    with pytest.raises(ast.tree.errors.TooManyChildren):
        node.add_child(ast.ArgNode('child'))
    assert node.num_children() == sum(1 for i in node.children())
    assert node.has_child0()
    assert node.has_child1()
    assert node.has_child2()
