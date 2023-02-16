import abc  # noqa: D100
import typing

import pydantic

from .entries import EntryDto


class ReferenceDto(pydantic.BaseModel):  # noqa: D101
    resource_id: str
    resource_version: typing.Optional[int]
    entry: EntryDto


class GetReferencedEntries(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def query(  # noqa: D102
        self,
        resource_id: str,
        entry_id: str,
    ) -> typing.Iterable[ReferenceDto]:
        pass
