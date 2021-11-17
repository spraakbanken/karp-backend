import abc
import typing

from karp.search.domain.search_service import IndexEntry


class PreProcessor(abc.ABC):
    @abc.abstractmethod
    def process(self, resource_id: str) -> typing.Iterable[IndexEntry]:
        raise NotImplementedError()

