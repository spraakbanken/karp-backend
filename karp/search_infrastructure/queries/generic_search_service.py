from collections import Counter
import typing

from karp.lex.application.repositories import (
    ResourceUnitOfWork,
    EntryUowRepositoryUnitOfWork,
)
from karp.lex.application.queries import (
    GetEntryRepositoryId,
)
from karp.search.application.queries import (
    EntryDto,
    QueryRequest,
    QueryResponse,
    QuerySplitResponse,
    SearchService,
    StatisticsDto,
)
from karp.search.domain import query_dsl


class GenericSearchService(SearchService):
    def __init__(
        self,
        get_entry_repo_id: GetEntryRepositoryId,
        entry_uow_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> None:
        self.get_entry_repo_id = get_entry_repo_id
        self.entry_uow_repo_uow = entry_uow_repo_uow
        self.parser = query_dsl.KarpQueryV6Parser(
            semantics=query_dsl.KarpQueryV6ModelBuilderSemantics()
        )

    def statistics(
        self, resource_id: str, field: str
    ) -> typing.Iterable[StatisticsDto]:
        entry_repo_id = self.get_entry_repo_id.query(resource_id)
        with self.entry_uow_repo_uow, self.entry_uow_repo_uow.repo.get_by_id(
            entry_repo_id
        ) as uw:
            all_entries = uw.repo.all_entries()
            values_of_field = (entry.body.get(field) for entry in all_entries)
            aggregate = Counter(values_of_field)
            return (
                StatisticsDto(value=key, count=count)
                for key, count in aggregate.items()
                if key is not None
            )

    def query(self, request: QueryRequest):
        if request.q:
            model = self.parser.parse(request.q)
        resource_id = request.resource_ids[0]
        entry_repo_id = self.get_entry_repo_id.query(resource_id)
        with self.entry_uow_repo_uow, self.entry_uow_repo_uow.repo.get_by_id(
            entry_repo_id
        ) as uw:
            all_entries = uw.repo.all_entries()
            hits = [
                EntryDto(
                    id=entry.entry_id,
                    version=entry.version,
                    last_modified=entry.last_modified,
                    last_modified_by=entry.last_modified_by,
                    resource=resource_id,
                    entry=entry.body,
                )
                for entry in all_entries
            ]

        if request.sort:
            field, order = request.sort[0].split("|")
            hits.sort(
                key=lambda entry: entry.entry.get(field, 0),
                reverse=order.lower() == "desc",
            )
        response = QueryResponse(
            hits=hits,
            total=len(hits),
        )
        if request.lexicon_stats:
            response.distribution = {resource_id: len(hits)}

        return response

    def query_split(self, request: QueryRequest):
        if request.q:
            model = self.parser.parse(request.q)
        dist = {}
        for resource_id in request.resource_ids:
            entry_repo_id = self.get_entry_repo_id.query(resource_id)
            with self.entry_uow_repo_uow, self.entry_uow_repo_uow.repo.get_by_id(
                entry_repo_id
            ) as uw:
                all_entries = uw.repo.all_entries()
                dist[resource_id] = [
                    EntryDto(
                        id=entry.entry_id,
                        version=entry.version,
                        last_modified=entry.last_modified,
                        last_modified_by=entry.last_modified_by,
                        resource=resource_id,
                        entry=entry.body,
                    )
                    for entry in all_entries
                ]

        return QuerySplitResponse(
            hits=[],
            total=0,
            distribution={resource: len(hits) for resource, hits in dist.items()},
        )

    def search_ids(self):
        pass
