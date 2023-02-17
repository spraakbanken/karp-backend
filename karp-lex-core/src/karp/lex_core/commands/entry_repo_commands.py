from typing import Literal, Optional  # noqa: D100

import pydantic
from karp.lex_core.value_objects import UniqueId, make_unique_id

from .base import Command


class CreateEntryRepository(Command):  # noqa: D101
    id: UniqueId = pydantic.Field(default_factory=make_unique_id)  # noqa: A003
    repository_type: str
    name: str
    connection_str: Optional[str] = None
    config: dict
    message: str
    user: str
    cmdtype: Literal["create_entry_repository"] = "create_entry_repository"

    @classmethod
    def from_dict(  # noqa: D102
        cls, data: dict, *, user: str, message: Optional[str] = None
    ) -> "CreateEntryRepository":
        return cls(
            # id=make_unique_id_str(),
            repository_type=data.pop("repository_type", "default"),
            name=data.pop("resource_id"),
            connection_str=data.pop("connection_str", None),
            config=data,
            user=user,
            message=message or "Entry repository created",
        )


class DeleteEntryRepository(Command):  # noqa: D101
    id: UniqueId  # noqa: A003
    version: int
    message: str
    user: str
    cmdtype: Literal["delete_entry_repository"] = "delete_entry_repository"
