import typing

from karp.lex.application.repositories import ResourceRepository


class GenericResourceViews:
    def __init__(self, resources: ResourceRepository) -> None:  # noqa: D107
        super().__init__()
        self._resources = resources

    def get_resource_config(self, resource_id: str) -> typing.Dict:  # noqa: D102
        return self._resource.by_resource_id(resource_id).config
