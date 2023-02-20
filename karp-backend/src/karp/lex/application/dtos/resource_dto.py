"""Resource DTO."""
from karp.lex_core.value_objects import UniqueIdStr

from .base import BaseModel, IdMixin


class ResourceDto(IdMixin, BaseModel):  # noqa: D101
    resource_id: str
    is_published: bool
    version: int
    name: str
    last_modified_by: str
    message: str
    last_modified: float
    config: dict
    entry_repository_id: UniqueIdStr
    discarded: bool
