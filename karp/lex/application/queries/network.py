import abc
import typing

import pydantic

from .entries import EntryDto


class ReferenceDto(pydantic.BaseModel):
    resource_id: str
    resource_version: typing.Optional[int]
    entry: EntryDto


class GetReferencedEntries(abc.ABC):
    @abc.abstractmethod
    def query(
        self,
        resource_id: str,
        entry_id: str,
    ) -> typing.Iterable[ReferenceDto]:
        pass
