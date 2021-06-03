from karp.services import unit_of_work
from . import es6_index


class Es6IndexUnitOfWork(unit_of_work.IndexUnitOfWork, index_type="es6_index"):
    def __init__(self) -> None:
        super().__init__()
        self._index = es6_index.Es6Index()

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
