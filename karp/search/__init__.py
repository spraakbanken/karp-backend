from typing import List

import injector

from karp.foundation.commands import CommandHandler
from karp.foundation.events import EventHandler
from karp.lex.domain import events as lex_events
from karp.search.domain import commands
from karp.search.application import handlers
from karp.search.application.queries import ResourceViews
from karp.search.application.repositories import IndexUnitOfWork, Index, IndexEntry
from karp.search.application.transformers import (
    EntryTransformer,
    PreProcessor,
)


class Search(injector.Module):
    @injector.provider
    def reindex_resource(
        self,
        index_uow: IndexUnitOfWork,
        pre_processor: PreProcessor,
        resource_views: ResourceViews,
    ) -> CommandHandler[commands.ReindexResource]:
        return handlers.ReindexResourceHandler(
            index_uow=index_uow,
            pre_processor=pre_processor,
            resource_views=resource_views,
        )

    @injector.multiprovider
    def create_index(
        self,
        index_uow: IndexUnitOfWork
    ) -> List[EventHandler[lex_events.ResourceCreated]]:
        return [
            handlers.CreateSearchServiceHandler(
                index_uow
            )
        ]

    @injector.multiprovider
    def publish_index(
        self,
        index_uow: IndexUnitOfWork
    ) -> List[EventHandler[lex_events.ResourcePublished]]:
        return [
            handlers.ResourcePublishedHandler(
                index_uow
            )
        ]

    @injector.multiprovider
    def add_entry(
        self,
        index_uow: IndexUnitOfWork,
        entry_transformer: EntryTransformer,
        resource_views: ResourceViews,
    ) -> List[EventHandler[lex_events.EntryAdded]]:
        return [
            handlers.EntryAddedHandler(
                index_uow=index_uow,
                entry_transformer=entry_transformer,
                resource_views=resource_views,
            )
        ]

    @injector.multiprovider
    def update_entry(
        self,
        index_uow: IndexUnitOfWork,
        entry_transformer: EntryTransformer,
        resource_views: ResourceViews,
    ) -> List[EventHandler[lex_events.EntryUpdated]]:
        return [
            handlers.EntryUpdatedHandler(
                index_uow=index_uow,
                entry_transformer=entry_transformer,
                resource_views=resource_views,
            )
        ]

    @injector.multiprovider
    def delete_entry(
        self,
        index_uow: IndexUnitOfWork,
        entry_transformer: EntryTransformer,
        resource_views: ResourceViews,
    ) -> List[EventHandler[lex_events.EntryDeleted]]:
        return [
            handlers.EntryDeletedHandler(
                index_uow=index_uow,
                entry_transformer=entry_transformer,
                resource_views=resource_views,
            )
        ]
