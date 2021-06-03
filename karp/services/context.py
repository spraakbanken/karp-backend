from typing import Dict

# from functools import singledispatch

# from karp.application.config import Config
from karp.domain import repository, index  # ResourceRepository
from karp.domain.auth_service import AuthService

# from karp.domain.services.auth.auth import Auth
# from karp.domain.models.search_service import SearchService

from . import unit_of_work


class Context:
    def __init__(
        self,
        resource_uow: unit_of_work.ResourceUnitOfWork,
        entry_uows: unit_of_work.EntriesUnitOfWork = None,
        resource_repo: repository.ResourceRepository = None,
        search_service: index.Index = None,
        auth_service: AuthService = None,
        index_uow: unit_of_work.IndexUnitOfWork = None,
        entry_uow_factory: unit_of_work.EntryUowFactory = None,
    ):
        self.resource_uow = resource_uow
        self.entry_uows = entry_uows
        self.resource_repo = resource_repo
        self.search_service = search_service
        self.auth_service = auth_service
        self.index_uow = index_uow
        self.entry_uow_factory = entry_uow_factory

    def __repr__(self):
        return f"Context(resource_repo={self.resource_repo!r})"

    def collect_new_events(self):
        yield from self.resource_uow.collect_new_events()
        yield from self.entry_uows.collect_new_events()
        # yield from self.index_uow.collect_new_events()


# @singledispatch
# def create_context(config: Config) -> Context:
#     return Context()
