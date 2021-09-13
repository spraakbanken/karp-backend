from karp.services import unit_of_work
from . import es6_index


class Es6IndexUnitOfWork(unit_of_work.IndexUnitOfWork, index_type="es6_index"):
    def __init__(self, es6_search_service: es6_index.Es6Index) -> None:
        super().__init__()
        self._index = es6_search_service

    @classmethod
    def from_dict(cls, **kwargs):
        return cls()

    def _commit(self):
        return super()._commit()

    def rollback(self):
        return super().rollback()

    @property
    def repo(self) -> es6_index.Es6Index:
        return self._index
