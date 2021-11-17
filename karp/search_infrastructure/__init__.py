import injector

from karp.lex.application.queries import GetReferencedEntries, GetEntryRepositoryId
from karp.lex.application.repositories import ResourceUnitOfWork, EntryUowRepositoryUnitOfWork
from karp.search.application.queries import GetResourceConfig
from karp.search.application.repositories import SearchServiceUnitOfWork

from karp.search.application.transformers import (
    EntryTransformer,
    PreProcessor,
)
from karp.search_infrastructure.queries import GenericGetResourceConfig
from karp.search_infrastructure.transformers import (
    GenericEntryTransformer,
    GenericPreProcessor,
)


class SearchInterface(injector.Module):
    @injector.provider
    def entry_transformer(
        self,
        search_service_uow: SearchServiceUnitOfWork,
        resource_uow: ResourceUnitOfWork,
        entry_uow_repo_uow: EntryUowRepositoryUnitOfWork,
        get_referenced_entries: GetReferencedEntries,
    ) -> EntryTransformer:
        return GenericEntryTransformer(
            search_service_uow=search_service_uow,
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


class GenericSearchInterface(injector.Module):
    @injector.provider
    def get_resource_config(self, resource_uow: ResourceUnitOfWork) -> GetResourceConfig:
        return GenericGetResourceConfig(
            resource_uow=resource_uow
        )
