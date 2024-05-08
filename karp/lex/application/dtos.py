"""DTOs for some requests."""

import typing

from karp.foundation.value_objects import unique_id
from karp.lex.domain.dtos import BaseModel, IdMixin
from karp.lex.domain.entities.entry import EntryOp


class EntryDiffRequest(IdMixin, BaseModel):
    resource_id: str
    from_version: typing.Optional[int] = None
    to_version: typing.Optional[int] = None
    from_date: typing.Optional[float] = None
    to_date: typing.Optional[float] = None
    entry: typing.Optional[typing.Dict] = None


class EntryHistoryRequest(BaseModel):
    resource_id: str
    user_id: typing.Optional[str] = None
    entry_id: typing.Optional[unique_id.UniqueIdStr] = None
    from_date: typing.Optional[float] = None
    to_date: typing.Optional[float] = None
    from_version: typing.Optional[int] = None
    to_version: typing.Optional[int] = None
    current_page: int = 0
    page_size: int = 100


class EntryDiffDto(BaseModel):
    diff: typing.Any
    from_version: typing.Optional[int]
    to_version: typing.Optional[int]


class HistoryDto(IdMixin, BaseModel):
    timestamp: float
    message: str
    version: int
    op: EntryOp
    user_id: str
    diff: list[dict]
    entry: dict


class GetHistoryDto(BaseModel):
    history: list[HistoryDto]
    total: int
