import typing  # noqa: D100, I001
from karp.foundation.value_objects import unique_id
from karp.lex.application.repositories import ResourceUnitOfWork
from karp.search.application.queries import ResourceViews


class GenericResourceViews(ResourceViews):  # noqa: D101
    def __init__(self, resource_uow: ResourceUnitOfWork) -> None:  # noqa: D107
        super().__init__()
        self._resource_uow = resource_uow

    def get_resource_config(self, resource_id: str) -> typing.Dict:  # noqa: D102
        with self._resource_uow as uw:
            return uw.repo.by_resource_id(resource_id).config

    def get_resource_ids(self, repo_id: unique_id.UniqueId) -> typing.List[str]:  # noqa: D102
        with self._resource_uow as uw:
            return [
                resource.resource_id
                for resource in uw.repo.get_all_resources()
                if resource.entry_repository_id == repo_id
            ]
