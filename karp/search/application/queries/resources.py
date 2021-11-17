import abc
import typing


class GetResourceConfig(abc.ABC):
    @abc.abstractmethod
    def query(self, resource_id: str) -> typing.Dict:
        raise NotImplementedError()
