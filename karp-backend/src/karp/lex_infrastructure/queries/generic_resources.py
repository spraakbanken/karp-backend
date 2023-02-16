from karp.foundation.value_objects import UniqueId  # noqa: D100
from karp.lex.application.queries import GetEntryRepositoryId
from karp.lex.application.repositories import ResourceUnitOfWork


class GenericGetEntryRepositoryId(GetEntryRepositoryId):  # noqa: D101
    def __init__(self, resource_uow: ResourceUnitOfWork) -> None:  # noqa: D107
        super().__init__()
        self._resource_uow = resource_uow

    def query(self, resource_id: str) -> UniqueId:  # noqa: D102
        with self._resource_uow as uw:
            return uw.repo.by_resource_id(resource_id).entry_repository_id
