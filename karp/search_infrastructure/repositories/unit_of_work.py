from karp import search
from .sql_search_service import SqlSearchService


class SqlSearchServiceUnitOfWork(search.IndexUnitOfWork):
    def __init__(self, session_factory):
        # session_factory=DEFAULT_SESSION_FACTORY):
        self.session_factory = session_factory
        self._index = SqlSearchService()

    def _commit(self):
        pass

    def rollback(self):
        pass

    @property
    def repo(self):
        if not self._index:
            raise RuntimeError()
        return self._index
