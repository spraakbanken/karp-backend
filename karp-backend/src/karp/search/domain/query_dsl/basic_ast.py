from typing import Iterable, TypeVar  # noqa: D100

from .node import Node

AnyValue = TypeVar("AnyValue", str, int, float)


class Ast:  # noqa: D101
    def __init__(self, root: Node = None):  # noqa: D107, ANN204
        self.root = root

    def __repr__(self):  # noqa: ANN204, D105
        return "<Tree root={}>".format(repr(self.root))

    def is_empty(self) -> bool:  # noqa: D102
        return self.root is None

    def pprint(self):  # noqa: ANN201, D102
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

    def gen_stream(self) -> Iterable[Node]:  # noqa: D102
        if not self.is_empty():
            yield from self.root.gen_stream()
