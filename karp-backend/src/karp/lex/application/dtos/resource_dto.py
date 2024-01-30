"""Resource DTO."""

import pydantic
from karp.lex_core import alias_generators
from karp.lex_core.value_objects import UniqueIdStr


class ResourceDto(pydantic.BaseModel):  # noqa: D101
    class Config:  # noqa: D106
        alias_generator = alias_generators.to_lower_camel

    id: UniqueIdStr  # noqa: A003
    resource_id: str
    is_published: bool
    version: int
    name: str
    last_modified_by: str
    message: str
    last_modified: float
    config: dict
    discarded: bool
