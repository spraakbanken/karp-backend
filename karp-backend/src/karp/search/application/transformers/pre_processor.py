import abc  # noqa: D100
import typing

from karp.search.application.repositories import IndexEntry


class PreProcessor(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def process(self, resource_id: str) -> typing.Iterable[IndexEntry]:  # noqa: D102
        raise NotImplementedError()
