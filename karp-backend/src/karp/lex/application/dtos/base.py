"""Base for Data Transfer Objects (dto)."""
import pydantic
from karp.lex_core import alias_generators
from karp.lex_core.value_objects import UniqueIdStr


class BaseModel(pydantic.BaseModel):  # noqa: D101
    class Config:  # noqa: D106
        # arbitrary_types_allowed = True
        alias_generator = alias_generators.to_lower_camel


class IdMixin(BaseModel):  # noqa: D101
    id: UniqueIdStr  # noqa: A003
