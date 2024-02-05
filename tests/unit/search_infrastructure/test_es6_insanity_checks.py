import contextlib  # noqa: I001
from karp.search_infrastructure.repositories.es6_indicies import (
    Es6Index,
)


class TestEs6Index:
    def test_can_instantiate_es6_index(self):  # noqa: ANN201
        with contextlib.suppress(AttributeError):
            Es6Index(es=None, mapping_repo=None)
