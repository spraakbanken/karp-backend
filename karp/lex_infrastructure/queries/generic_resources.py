from karp.foundation.value_objects import UniqueId
from karp.lex.application.queries import GetEntryRepositoryId
from karp.lex.application.repositories import ResourceUnitOfWork


class GenericGetEntryRepositoryId(GetEntryRepositoryId):
    def __init__(self, resource_uow: ResourceUnitOfWork) -> None:
        super().__init__()
        self._resource_uow = resource_uow

    def query(self, resource_id: str) -> UniqueId:
        with self._resource_uow as uw:
            return uw.repo.by_resource_id(resource_id).entry_repository_id
