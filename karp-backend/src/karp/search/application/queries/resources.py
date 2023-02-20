import abc  # noqa: D100
import typing

from karp.lex_core.value_objects import unique_id


class ResourceViews(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def get_resource_config(self, resource_id: str) -> typing.Dict:  # noqa: D102
        raise NotImplementedError()

    @abc.abstractmethod
    def get_resource_ids(  # noqa: D102
        self, repo_id: unique_id.UniqueIdStr
    ) -> typing.List[str]:
        raise NotImplementedError()
