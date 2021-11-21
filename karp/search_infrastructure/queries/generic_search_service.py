from collections import Counter
import typing

from karp.lex.application.repositories import (
    ResourceUnitOfWork,
    EntryUowRepositoryUnitOfWork,
)
from karp.lex.application.queries import (
    GetEntryRepositoryId,
)
from karp.search.application.queries import SearchService, StatisticsDto


class GenericSearchService(SearchService):
    def __init__(
        self,
        get_entry_repo_id: GetEntryRepositoryId,
        entry_uow_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> None:
        self.get_entry_repo_id = get_entry_repo_id
        self.entry_uow_repo_uow = entry_uow_repo_uow

    def statistics(self, resource_id: str, field: str) -> typing.List[StatisticsDto]:
        entry_repo_id = self.get_entry_repo_id.query(resource_id)
        with self.entry_uow_repo_uow, self.entry_uow_repo_uow.repo.get_by_id(entry_repo_id) as uw:
            all_entries = uw.repo.all_entries()
            values_of_field = (entry.body.get(field) for entry in all_entries)
            aggregate = Counter(values_of_field)
            return (
                StatisticsDto(value=key, count=count)
                for key, count in aggregate.items()
                if key is not None
            )

    def query(self):
        pass

    def query_split(self):
        pass

    def search_ids(self):
        pass
