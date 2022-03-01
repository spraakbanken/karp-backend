import elasticsearch
import injector
from sqlalchemy.orm import sessionmaker
import logging

from karp.foundation.events import EventBus
from karp.lex.application.queries import (
    GetReferencedEntries,
    GetEntryRepositoryId,
    ReadOnlyResourceRepository,
    EntryViews,
)
from karp.lex.application.repositories import (
    ResourceUnitOfWork,
    EntryUowRepositoryUnitOfWork,
)
from karp import lex, search
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
    GenericPreviewEntry,
    GenericResourceViews,
    GenericSearchService,
    Es6SearchService,
)
from karp.search_infrastructure.transformers import (
    GenericEntryTransformer,
    GenericPreProcessor,
)
from karp.search_infrastructure.repositories import (
    # SqlIndexUnitOfWork,
    NoOpIndexUnitOfWork,
    Es6IndexUnitOfWork,
)


logger = logging.getLogger(__name__)


class SearchInfrastructure(injector.Module):
    @injector.provider
    def entry_transformer(
        self,
        index_uow: IndexUnitOfWork,
        resource_repo: lex.ReadOnlyResourceRepository,
        entry_views: EntryViews,
        get_referenced_entries: GetReferencedEntries,
    ) -> EntryTransformer:
        return GenericEntryTransformer(
            index_uow=index_uow,
            resource_repo=resource_repo,
            entry_views=entry_views,
            get_referenced_entries=get_referenced_entries,
        )

    @injector.provider
    def pre_processor(
        self,
        entry_transformer: EntryTransformer,
        entry_views: EntryViews,
    ) -> PreProcessor:
        return GenericPreProcessor(
            entry_transformer=entry_transformer,
            entry_views=entry_views,
        )

    @injector.provider
    def preview_entry(
        self,
        entry_transformer: EntryTransformer,
        resource_uow: lex.ResourceUnitOfWork,
    ) -> search.PreviewEntry:
        return GenericPreviewEntry(
            entry_transformer=entry_transformer,
            resource_uow=resource_uow,
        )


class GenericSearchInfrastructure(injector.Module):
    @injector.provider
    def get_resource_config(self, resource_uow: lex.ResourceUnitOfWork) -> ResourceViews:
        return GenericResourceViews(
            resource_uow=resource_uow
        )


class GenericSearchIndexMod(injector.Module):

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


class Es6SearchIndexMod(injector.Module):

    @injector.provider
    def es6_search_service(
        self,
        es: elasticsearch.Elasticsearch,
    ) -> SearchService:
        return Es6SearchService(es=es)

    @injector.provider
    def es6_index_uow(
        self,
        es: elasticsearch.Elasticsearch,
        event_bus: EventBus,
    ) -> IndexUnitOfWork:
        return Es6IndexUnitOfWork(
            es=es,
            event_bus=event_bus
        )
