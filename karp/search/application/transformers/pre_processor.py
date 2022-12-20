import abc
import typing

from karp.search.application.repositories import IndexEntry


class PreProcessor(abc.ABC):
    @abc.abstractmethod
    def process(self, resource_id: str) -> typing.Iterable[IndexEntry]:
        raise NotImplementedError()
