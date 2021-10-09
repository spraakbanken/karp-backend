class Node:
    def __init__(self, type_, arity: int, value=None):
        self.type = type_
        self.arity = arity
        self.value = value
        self.children = []

    def __repr__(self):
        return "<Node {t} {v} {c}>".format(t=self.type, v=self.value, c=self.children)

    def _pprint(self, level):
        fill = " "
        print(
            "{indent} Node {t} {v}".format(
                indent=fill * level, t=self.type, v=self.value
            )
        )
        for child in self.children:
            child._pprint(level + 1)

    def pprint(self, level: int = 0):
        self._pprint(level)

    def add_child(self, child):
        self.children.append(child)

    def n_children(self) -> int:
        return len(self.children)

    def gen_stream(self):
        yield self
        for child in self.children:
            yield from child.gen_stream()


def create_unary_node(type_, value=None):
    return Node(type_, 1, value)


def create_binary_node(type_, value=None):
    return Node(type_, 2, value)
