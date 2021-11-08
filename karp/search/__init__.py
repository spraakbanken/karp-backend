from typing import List

import injector

from karp.foundation.events import EventHandler
from karp.lex.domain import events as lex_events
from karp.search.application import handlers
from karp.search.application.repositories import SearchServiceUnitOfWork
from karp.search.application.transformers.entry_transformer import EntryTransformer


class Search(injector.Module):
    @injector.multiprovider
    def create_index(
        self,
        search_service_uow: SearchServiceUnitOfWork
    ) -> List[EventHandler[lex_events.ResourceCreated]]:
        return [
            handlers.CreateSearchServiceHandler(
                search_service_uow
            )
        ]

    @injector.multiprovider
    def publish_index(
        self,
        search_service_uow: SearchServiceUnitOfWork
    ) -> List[EventHandler[lex_events.ResourcePublished]]:
        return [
            handlers.ResourcePublishedHandler(
                search_service_uow
            )
        ]

    @injector.multiprovider
    def add_entry(
        self,
        search_service_uow: SearchServiceUnitOfWork,
        entry_transformer: EntryTransformer,
    ) -> List[EventHandler[lex_events.EntryAdded]]:
        return [
            handlers.EntryAddedHandler(
                search_service_uow=search_service_uow,
                entry_transformer=entry_transformer,
            )
        ]

    @injector.multiprovider
    def update_entry(
        self,
        search_service_uow: SearchServiceUnitOfWork,
        entry_transformer: EntryTransformer,
    ) -> List[EventHandler[lex_events.EntryUpdated]]:
        return [
            handlers.EntryUpdatedHandler(
                search_service_uow=search_service_uow,
                entry_transformer=entry_transformer,
            )
        ]
