import logging
import typing
from typing import Callable, Dict, List, Optional, Tuple, TypeVar

import pydantic

from karp.search.domain.query import Query

logger = logging.getLogger(__name__)


class QueryRequest(pydantic.BaseModel):  # pylint: disable=no-member
    resource_ids: typing.List[str]
    q: typing.Optional[str] = None
    from_: int = 0
    size: int = 25
    lexicon_stats: bool = True
    sort: List[str] = pydantic.Field(default_factory=list)

    @pydantic.validator("resource_ids", pre=True)
    @classmethod
    def split_str(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v
