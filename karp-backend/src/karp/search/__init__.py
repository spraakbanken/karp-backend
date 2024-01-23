from typing import List  # noqa: I001

import injector

from karp.command_bus import CommandHandler
from karp.foundation.events import EventHandler
from karp.lex.domain import events as lex_events
from karp.search.domain import commands
from karp.search.domain.errors import IncompleteQuery
from karp.search.application.use_cases import (
    CreateSearchServiceHandler,
    DeletingIndex,
    EntryAddedHandler,
    EntryDeletedHandler,
    EntryUpdatedHandler,
    ReindexingResource,
    ResourcePublishedHandler,
)
from karp.search.application.queries import QueryRequest
from karp.search.application.repositories import (
    IndexUnitOfWork,
    IndexEntry,
)

__all__ = [
    "IndexUnitOfWork",
    "IndexEntry",
]

from karp.search.generic_resources import GenericResourceViews
from karp.search_infrastructure.transformers.generic_entry_transformer import (
    GenericEntryTransformer,
)
from karp.search_infrastructure.transformers.generic_pre_processor import GenericPreProcessor


class Search(injector.Module):  # noqa: D101
    @injector.provider
    def reindex_resource(  # noqa: D102
        self,
        index_uow: IndexUnitOfWork,
        pre_processor: GenericPreProcessor,
        resource_views: GenericResourceViews,
    ) -> CommandHandler[commands.ReindexResource]:
        return ReindexingResource(
            index_uow=index_uow,
            pre_processor=pre_processor,
            resource_views=resource_views,
        )

    @injector.multiprovider
    def create_index(  # noqa: D102
        self, index_uow: IndexUnitOfWork
    ) -> List[EventHandler[lex_events.ResourceCreated]]:
        return [CreateSearchServiceHandler(index_uow)]

    @injector.multiprovider
    def deleting_index(  # noqa: D102
        self,
        index_uow: IndexUnitOfWork,
    ) -> List[EventHandler[lex_events.ResourceDiscarded]]:
        return [DeletingIndex(index_uow=index_uow)]

    @injector.multiprovider
    def publish_index(  # noqa: D102
        self, index_uow: IndexUnitOfWork
    ) -> List[EventHandler[lex_events.ResourcePublished]]:
        return [ResourcePublishedHandler(index_uow)]

    @injector.multiprovider
    def add_entry(  # noqa: D102
        self,
        index_uow: IndexUnitOfWork,
        entry_transformer: GenericEntryTransformer,
        resource_views: GenericResourceViews,
    ) -> List[EventHandler[lex_events.EntryAdded]]:
        return [
            EntryAddedHandler(
                index_uow=index_uow,
                entry_transformer=entry_transformer,
                resource_views=resource_views,
            )
        ]

    @injector.multiprovider
    def update_entry(  # noqa: D102
        self,
        index_uow: IndexUnitOfWork,
        entry_transformer: GenericEntryTransformer,
        resource_views: GenericResourceViews,
    ) -> List[EventHandler[lex_events.EntryUpdated]]:
        return [
            EntryUpdatedHandler(
                index_uow=index_uow,
                entry_transformer=entry_transformer,
                resource_views=resource_views,
            )
        ]

    @injector.multiprovider
    def delete_entry(  # noqa: D102
        self,
        index_uow: IndexUnitOfWork,
        entry_transformer: GenericEntryTransformer,
        resource_views: GenericResourceViews,
    ) -> List[EventHandler[lex_events.EntryDeleted]]:
        return [
            EntryDeletedHandler(
                index_uow=index_uow,
                entry_transformer=entry_transformer,
                resource_views=resource_views,
            )
        ]
