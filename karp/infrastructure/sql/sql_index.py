from typing import List, Optional

from karp.domain.models.search_service import SearchService, IndexEntry
from karp.domain.models.resource import Resource
from karp.domain.models.entry import Entry


class SqlSearchService(SearchService, search_service_type="sql_search_service", is_default=True):
    def add_entries(self, resource_id, entries: List[IndexEntry]):
        pass

    def delete_entry(
        self,
        resource: Resource,
        *,
        entry: Optional[Entry] = None,
        entry_id: Optional[str] = None
    ):
        pass
