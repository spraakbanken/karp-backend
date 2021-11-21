import injector
from sqlalchemy.orm import sessionmaker

from karp.foundation.events import EventBus
from karp.lex.application.queries import (
    GetReferencedEntries,
    GetEntryRepositoryId,
)
from karp.lex.application.repositories import (
    ResourceUnitOfWork,
    EntryUowRepositoryUnitOfWork,
)
from karp.search.application.queries import (
    ResourceViews,
    SearchService,
)
from karp.search.application.repositories import IndexUnitOfWork

from karp.search.application.transformers import (
    EntryTransformer,
    PreProcessor,
)
from karp.search_infrastructure.queries import (
    GenericResourceViews,
    GenericSearchService,
)
from karp.search_infrastructure.transformers import (
    GenericEntryTransformer,
    GenericPreProcessor,
)
from karp.search_infrastructure.repositories import (
    # SqlIndexUnitOfWork,
    NoOpIndexUnitOfWork,
)


class SearchInfrastructure(injector.Module):
    @injector.provider
    def entry_transformer(
        self,
        index_uow: IndexUnitOfWork,
        resource_uow: ResourceUnitOfWork,
        entry_uow_repo_uow: EntryUowRepositoryUnitOfWork,
        get_referenced_entries: GetReferencedEntries,
    ) -> EntryTransformer:
        return GenericEntryTransformer(
            index_uow=index_uow,
            resource_uow=resource_uow,
            entry_uow_repo_uow=entry_uow_repo_uow,
            get_referenced_entries=get_referenced_entries,
        )

    @injector.provider
    def pre_processor(
        self,
        entry_transformer: EntryTransformer,
        get_entry_repo_id: GetEntryRepositoryId,
        entry_uow_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> PreProcessor:
        return GenericPreProcessor(
            entry_transformer=entry_transformer,
            get_entry_repo_id=get_entry_repo_id,
            entry_uow_repo_uow=entry_uow_repo_uow,
        )


class GenericSearchInfrastructure(injector.Module):
    @injector.provider
    def get_resource_config(self, resource_uow: ResourceUnitOfWork) -> ResourceViews:
        return GenericResourceViews(
            resource_uow=resource_uow
        )


class SearchServiceMod(injector.Module):
    def __init__(self, search_service: str):
        pass

    @injector.provider
    def generic_search_service(
        self,
        get_entry_repo_id: GetEntryRepositoryId,
        entry_uow_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> SearchService:
        return GenericSearchService(
            get_entry_repo_id=get_entry_repo_id,
            entry_uow_repo_uow=entry_uow_repo_uow,
        )

    @injector.provider
    def noop_index_uow(
        self,
    ) -> IndexUnitOfWork:
        return NoOpIndexUnitOfWork()
