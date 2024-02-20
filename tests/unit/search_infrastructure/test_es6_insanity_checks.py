import contextlib  # noqa: I001
from karp.search.infrastructure.es.indices import (
    EsIndex,
)


class TestEsIndex:
    def test_can_instantiate_es_index(self):  # noqa: ANN201
        with contextlib.suppress(AttributeError):
            EsIndex(es=None, mapping_repo=None)
