

class Node:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value
        self.children = []

    def __repr__(self):
        return '<Node {t} {v} {c}>'.format(
            t=self.type,
            v=self.value,
            c=self.children
        )

    def _pprint(self, level):
        fill = ' '
        print('{indent} Node {t} {v}'.format(
            indent=fill*level,
            t=self.type,
            v=self.value
        ))
        for child in self.children:
            child._pprint(indent+1)

    def pprint(self, level: int = 0):
        self._pprint(level)

    def add_child(self, child):
        self.children.append(child)

    def gen_stream(self):
        yield self
        for child in self.children:
            yield from child.gen_stream()
