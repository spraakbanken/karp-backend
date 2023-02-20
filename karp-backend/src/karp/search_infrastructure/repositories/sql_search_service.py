import logging  # noqa: D100, I001
from typing import Dict, Optional, Iterable

from karp.search.domain import query_dsl
from karp.search.application.repositories import Index, IndexUnitOfWork, IndexEntry
from karp.lex.domain.entities.entry import Entry
from karp.lex.domain.entities.resource import Resource

logger = logging.getLogger(__name__)


class SqlSearchService(Index):  # noqa: D101
    def __init__(self):  # noqa: D107, ANN204
        self.parser = query_dsl.KarpQueryV6Parser(
            semantics=query_dsl.KarpQueryV6ModelBuilderSemantics()
        )

    def create_index(  # noqa: D102, ANN201
        self, resource_id: str, resource_config: Dict
    ):
        pass

    def publish_index(self, resource_id: str):  # noqa: ANN201, D102
        pass

    def query(self):  # noqa: ANN201, D102
        pass

    def query_split(self):  # noqa: ANN201, D102
        pass

    def search_ids(self):  # noqa: ANN201, D102
        pass

    def statistics(self):  # noqa: ANN201, D102
        pass

    def add_entries(  # noqa: D102, ANN201
        self, resource_id, entries: Iterable[IndexEntry]
    ):
        pass

    def delete_entry(  # noqa: ANN201, D102
        self,
        resource: Resource,
        *,
        entry: Optional[Entry] = None,
        entry_id: Optional[str] = None,
    ):
        pass


class SqlIndexUnitOfWork(IndexUnitOfWork):  # noqa: D101
    @classmethod
    def from_dict(cls, **kwargs):  # noqa: ANN206, ANN003, D102
        logger.debug(f"SqlIndexUnitOfWork.from_dict: kwargs = {kwargs}")
        return cls(**kwargs)

    def __init__(  # noqa: D107, ANN204
        self,
        session_factory,
        event_bus,
    ):
        super().__init__(event_bus)
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
