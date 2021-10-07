from typing import Dict, List, Optional

# from karp.domain.models.search_service import SearchService, IndexEntry
from karp.domain import index
from karp.domain.models.entry import Entry
from karp.domain.models.resource import Resource


class SqlSearchService(index.Index):
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

    def add_entries(self, resource_id, entries: List[index.IndexEntry]):
        pass

    def delete_entry(
        self,
        resource: Resource,
        *,
        entry: Optional[Entry] = None,
        entry_id: Optional[str] = None
    ):
        pass
