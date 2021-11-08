import injector
from karp.lex.application.repositories.unit_of_work import ResourceUnitOfWork
from karp.search.application.repositories.search_service_unit_of_work import SearchServiceUnitOfWork

from karp.search.application.transformers import EntryTransformer
from karp.search_infrastructure.transformers import GenericEntryTransformer


class SearchInterface(injector.Module):
    @injector.provider
    def entry_transformer(
        self,
        search_service_uow: SearchServiceUnitOfWork,
        resource_uow: ResourceUnitOfWork,
    ) -> EntryTransformer:
        return GenericEntryTransformer(
            search_service_uow=search_service_uow,
            resource_uow=resource_uow,
        )
