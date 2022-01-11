from typing import Iterable, TypeVar

from .node import Node

AnyValue = TypeVar("AnyValue", str, int, float)


class Ast:
    def __init__(self, root: Node = None):
        self.root = root

    def __repr__(self):
        return "<Tree root={}>".format(repr(self.root))

    def is_empty(self) -> bool:
        return self.root is None

    def pprint(self):
        print("<Tree root=")
        if not self.is_empty():
            self.root.pprint(1)
        print(">")

    # def validate_arity(self) -> Tuple[bool, str]:
    #     if self.is_empty():
    #         return True, "This tree is empty."
    #
    #     result = []
    #     self.root.validate_arity(result)
    #     if not result:
    #         return True, None
    #     else:
    #         return False, ', '.join(result)

    def gen_stream(self) -> Iterable[Node]:
        if not self.is_empty():
            yield from self.root.gen_stream()
