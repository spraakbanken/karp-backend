from typing import List

import injector

from karp.foundation.events import EventHandler
from karp.lex.domain import events as lex_events
from karp.search.application import handlers
from karp.search.application.repositories import SearchServiceUnitOfWork


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
