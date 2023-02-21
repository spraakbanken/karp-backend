from typing import Literal  # noqa: D100

import pydantic
from karp.lex_core import alias_generators
from karp.utility import time


class Command(pydantic.BaseModel):  # noqa: D101
    timestamp: float = pydantic.Field(default_factory=time.utc_now)

    class Config:  # noqa: D106
        # arbitrary_types_allowed = True
        extra = "forbid"
        alias_generator = alias_generators.to_lower_camel


class ReindexResource(Command):  # noqa: D101
    resource_id: str
    cmdtype: Literal["reindex_resource"] = "reindex_resource"
