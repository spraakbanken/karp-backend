from typing import Dict

# from karp.application.config import Config
from karp.domain import index, repository  # ResourceRepository

from . import unit_of_work
from .auth_service import AuthService

# from functools import singledispatch


# from karp.domain.services.auth.auth import Auth
# from karp.domain.models.search_service import SearchService



class Context:
    def __init__(
        self,
        resource_uow: unit_of_work.ResourceUnitOfWork,
        entry_uows: unit_of_work.EntriesUnitOfWork,
        # resource_repo: repository.ResourceRepository,
        # search_service: index.Index,
        # auth_service: AuthService,
        index_uow: unit_of_work.IndexUnitOfWork,
        entry_uow_factory: unit_of_work.EntryUowFactory,
    ):
        self.resource_uow = resource_uow
        self.entry_uows = entry_uows
        # self.resource_repo = resource_repo
        # self.search_service = search_service
        # self.auth_service = auth_service
        self.index_uow = index_uow
        self.entry_uow_factory = entry_uow_factory

    def __repr__(self):
        return f"Context()"

    def collect_new_events(self):
        yield from self.resource_uow.collect_new_events()
        yield from self.entry_uows.collect_new_events()
        # yield from self.index_uow.collect_new_events()


# @singledispatch
# def create_context(config: Config) -> Context:
#     return Context()
