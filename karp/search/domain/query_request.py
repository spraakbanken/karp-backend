import logging
import typing
from typing import List

import pydantic

logger = logging.getLogger(__name__)


class QueryRequest(pydantic.BaseModel):
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
