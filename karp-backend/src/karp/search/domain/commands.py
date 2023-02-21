from typing import Literal  # noqa: D100

import pydantic
from karp import timings
from karp.lex_core import alias_generators


class Command(pydantic.BaseModel):  # noqa: D101
    timestamp: float = pydantic.Field(default_factory=timings.utc_now)

    class Config:  # noqa: D106
        # arbitrary_types_allowed = True
        extra = "forbid"
        alias_generator = alias_generators.to_lower_camel


class ReindexResource(Command):  # noqa: D101
    resource_id: str
    cmdtype: Literal["reindex_resource"] = "reindex_resource"
