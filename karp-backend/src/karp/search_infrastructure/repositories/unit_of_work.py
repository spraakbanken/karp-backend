from karp import search  # noqa: D100, I001
from .sql_search_service import SqlSearchService


class SqlSearchServiceUnitOfWork(search.IndexUnitOfWork):  # noqa: D101
    def __init__(self, session_factory):  # noqa: D107, ANN204
        # session_factory=DEFAULT_SESSION_FACTORY):
        self.session_factory = session_factory
        self._index = SqlSearchService()

    def _commit(self):  # noqa: ANN202
        pass

    def rollback(self):  # noqa: ANN201, D102
        pass

    @property
    def repo(self):  # noqa: ANN201, D102
        if not self._index:
            raise RuntimeError()
        return self._index
