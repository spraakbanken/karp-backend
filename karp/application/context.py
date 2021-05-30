# from functools import singledispatch

# from karp.application.config import Config
from karp.domain import repository  # ResourceRepository
from karp.domain.models.auth_service import AuthService

# from karp.domain.services.auth.auth import Auth
from karp.domain.models.search_service import SearchService


class Context:
    def __init__(
        self,
        resource_repo: repository.ResourceRepository = None,
        search_service: SearchService = None,
        auth_service: AuthService = None,
    ):
        self.resource_repo = resource_repo
        self.search_service = search_service
        self.auth_service = auth_service

    def __repr__(self):
        return f"Context(resource_repo={self.resource_repo!r})"


# @singledispatch
# def create_context(config: Config) -> Context:
#     return Context()
