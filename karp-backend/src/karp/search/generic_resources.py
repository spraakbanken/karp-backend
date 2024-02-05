import typing

from karp.lex_infrastructure import SqlResourceUnitOfWork


class GenericResourceViews:
    def __init__(self, resource_uow: SqlResourceUnitOfWork) -> None:  # noqa: D107
        super().__init__()
        self._resource_uow = resource_uow

    def get_resource_config(self, resource_id: str) -> typing.Dict:  # noqa: D102
        with self._resource_uow as uw:
            return uw.repo.by_resource_id(resource_id).config
