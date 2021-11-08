import injector

from karp.lex.application.queries import GetReferencedEntries
from karp.lex.application.repositories import ResourceUnitOfWork, EntryUowRepositoryUnitOfWork
from karp.lex.domain.entities import entry
from karp.search.application.repositories import SearchServiceUnitOfWork

from karp.search.application.transformers import EntryTransformer
from karp.search_infrastructure.transformers import GenericEntryTransformer


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
