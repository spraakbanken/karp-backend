class Node:  # noqa: D100, D101
    def __init__(self, type_, arity: int, value=None):  # noqa: D107, ANN204
        self.type = type_
        self.arity = arity
        self.value = value
        self.children = []

    def __repr__(self):  # noqa: ANN204, D105
        return "<Node {t} {v} {c}>".format(t=self.type, v=self.value, c=self.children)

    def _pprint(self, level):  # noqa: ANN202
        fill = " "
        print(
            "{indent} Node {t} {v}".format(
                indent=fill * level, t=self.type, v=self.value
            )
        )
        for child in self.children:
            child._pprint(level + 1)

    def pprint(self, level: int = 0):  # noqa: ANN201, D102
        self._pprint(level)

    def add_child(self, child):  # noqa: ANN201, D102
        self.children.append(child)

    def n_children(self) -> int:  # noqa: D102
        return len(self.children)

    def gen_stream(self):  # noqa: ANN201, D102
        yield self
        for child in self.children:
            yield from child.gen_stream()


def create_unary_node(type_, value=None):  # noqa: ANN201, D103
    return Node(type_, 1, value)


def create_binary_node(type_, value=None):  # noqa: ANN201, D103
    return Node(type_, 2, value)
