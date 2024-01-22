import abc  # noqa: D100, I001
import logging
import typing
from typing import Callable, Dict, List, Optional, Tuple, TypeVar  # noqa: F401

import pydantic

from karp.search.domain.query import Query  # noqa: F401

logger = logging.getLogger(__name__)


# class EntryDto(pydantic.BaseModel):  # noqa: D101
#     id: str  # noqa: A003
#     version: int
#     last_modified: float
#     last_modified_by: str
#     resource: str
#     entry: typing.Dict


class StatisticsDto(pydantic.BaseModel):  # noqa: D101
    value: str
    count: int


class QueryRequest(pydantic.BaseModel):  # pylint: disable=no-member  # noqa: D101
    resource_ids: typing.List[str]
    q: typing.Optional[str] = None
    from_: int = 0
    size: int = 25
    lexicon_stats: bool = True
    sort: List[str] = pydantic.Field(default_factory=list)

    @pydantic.validator("resource_ids", pre=True)
    @classmethod
    def split_str(cls, v):  # noqa: ANN206, D102
        if isinstance(v, str):
            return v.split(",")
        return v
