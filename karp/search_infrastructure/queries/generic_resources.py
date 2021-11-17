import typing
from karp.lex.application.repositories import ResourceUnitOfWork
from karp.search.application.queries import GetResourceConfig


class GenericGetResourceConfig(GetResourceConfig):
    def __init__(self, resource_uow: ResourceUnitOfWork) -> None:
        super().__init__()
        self._resource_uow = resource_uow

    def query(self, resource_id: str) -> typing.Dict:
        with self._resource_uow as uw:
            return uw.repo.by_resource_id(resource_id).config
