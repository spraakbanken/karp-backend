import logging
from typing import Dict, Optional, Iterable

from karp.search.domain import query_dsl
from karp.search.application.repositories import Index, IndexUnitOfWork, IndexEntry
from karp.lex.domain.entities.entry import Entry
from karp.lex.domain.entities.resource import Resource

logger = logging.getLogger(__name__)


class SqlSearchService(Index):
    def __init__(self):
        self.seen = []
        self.parser = query_dsl.KarpQueryV6Parser(
            semantics=query_dsl.KarpQueryV6ModelBuilderSemantics()
        )

    def create_index(self, resource_id: str, resource_config: Dict):
        pass

    def publish_index(self, resource_id: str):
        pass

    def query(self):
        pass

    def query_split(self):
        pass

    def search_ids(self):
        pass

    def statistics(self):
        pass

    def add_entries(self, resource_id, entries: Iterable[IndexEntry]):
        pass

    def delete_entry(
        self,
        resource: Resource,
        *,
        entry: Optional[Entry] = None,
        entry_id: Optional[str] = None,
    ):
        pass


class SqlIndexUnitOfWork(IndexUnitOfWork):
    @classmethod
    def from_dict(cls, **kwargs):
        logger.debug(f"SqlIndexUnitOfWork.from_dict: kwargs = {kwargs}")
        return cls(**kwargs)

    def __init__(
        self,
        session_factory,
        event_bus,
    ):
        super().__init__(event_bus)
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
