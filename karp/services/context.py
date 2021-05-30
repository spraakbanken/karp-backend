from typing import Dict

# from functools import singledispatch

# from karp.application.config import Config
from karp.domain import repository  # ResourceRepository
from karp.domain.models.auth_service import AuthService

# from karp.domain.services.auth.auth import Auth
from karp.domain.models.search_service import SearchService

from . import unit_of_work


class Context:
    def __init__(
        self,
        resource_uow: unit_of_work.ResourceUnitOfWork,
        entry_uows: Dict[str, unit_of_work.EntryUnitOfWork] = None,
        resource_repo: repository.ResourceRepository = None,
        search_service: SearchService = None,
        auth_service: AuthService = None,
    ):
        self.resource_uow = resource_uow
        self.entry_uows = entry_uows or {}
        self.resource_repo = resource_repo
        self.search_service = search_service
        self.auth_service = auth_service

    def __repr__(self):
        return f"Context(resource_repo={self.resource_repo!r})"

    def collect_new_events(self):
        for uow in [self.resource_uow]:
            yield from uow.collect_new_events()


# @singledispatch
# def create_context(config: Config) -> Context:
#     return Context()
