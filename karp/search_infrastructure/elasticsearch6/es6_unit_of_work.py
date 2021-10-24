from karp.search.application import repositories

from . import es6_search_service


class Es6SearchServiceUnitOfWork(
    repositories.SearchServiceUnitOfWork
):
    def __init__(self, es6_search_service: es6_search_service.Es6SearchService) -> None:
        super().__init__()
        self._search_service = es6_search_service

    @classmethod
    def from_dict(cls, **kwargs):
        return cls()

    def _commit(self):
        return super()._commit()

    def rollback(self):
        return super().rollback()

    @property
    def repo(self) -> es6_search_service.Es6SearchService:
        return self._search_service
