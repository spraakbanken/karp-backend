import abc  # noqa: D100
import typing

from karp.foundation.value_objects import unique_id


class ResourceViews(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def get_resource_config(self, resource_id: str) -> typing.Dict:  # noqa: D102
        raise NotImplementedError()

    @abc.abstractmethod
    def get_resource_ids(self, repo_id: unique_id.UniqueId) -> typing.List[str]:  # noqa: D102
        raise NotImplementedError()
