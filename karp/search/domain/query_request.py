import logging
import typing
from typing import List

import pydantic

from karp.search.domain.query_dsl.karp_query_model import ModelBase

logger = logging.getLogger(__name__)


class QueryRequest(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    resources: typing.List[str]
    q: str | ModelBase = ""
    from_: int = 0
    size: int = 25
    lexicon_stats: bool = True
    highlight: bool = False
    sort: List[str] = pydantic.Field(default_factory=list)
    path: typing.Optional[str] = None

    @pydantic.field_validator("q", mode="before")
    @classmethod
    def remove_none(cls, v):
        if v is None:
            return ""
        return v

    @pydantic.field_validator("resources", mode="before")
    @classmethod
    def split_str(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v
