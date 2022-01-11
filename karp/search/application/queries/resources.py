import abc
import typing

from karp.foundation.value_objects import unique_id


class ResourceViews(abc.ABC):
    @abc.abstractmethod
    def get_resource_config(self, resource_id: str) -> typing.Dict:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_resource_ids(self, repo_id: unique_id.UniqueId) -> typing.List[str]:
        raise NotImplementedError()
