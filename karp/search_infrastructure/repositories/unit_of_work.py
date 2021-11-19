from karp.search.application import unit_of_work
from .sql_search_service import SqlSearchService


class SqlSearchServiceUnitOfWork(unit_of_work.SearchServiceUnitOfWork):
    @classmethod
    def from_dict(cls, **kwargs):
        print(f"SqlIndexUnitOfWork.from_dict: kwargs = {kwargs}")
        return cls()

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
