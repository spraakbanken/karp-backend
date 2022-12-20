from typing import Dict, Optional

import pydantic

from karp.foundation.value_objects import UniqueId, make_unique_id

from .base import Command


class CreateEntryRepository(Command):
    entity_id: UniqueId = pydantic.Field(default_factory=make_unique_id)
    repository_type: str
    name: str
    connection_str: Optional[str] = None
    config: Dict
    message: str
    user: str

    @classmethod
    def from_dict(cls, data: Dict, *, user: str, message: Optional[str] = None):
        return cls(
            entity_id=make_unique_id(),
            repository_type=data.pop("repository_type", "default"),
            name=data.pop("resource_id"),
            connection_str=data.pop("connection_str", None),
            config=data,
            user=user,
            message=message or "Entry repository created",
        )


class DeleteEntryRepository(Command):
    entity_id: UniqueId
    message: str
    user: str
