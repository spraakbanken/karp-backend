from typing import Generic, Iterable, Literal, Optional, TypeVar  # noqa: D100

import pydantic
from karp.lex_core.value_objects import UniqueIdStr, make_unique_id_str
from pydantic.generics import GenericModel

from .base import Command

T = TypeVar("T")


class GenericAddEntry(GenericModel, Generic[T], Command):  # noqa: D101
    entity_id: UniqueIdStr = pydantic.Field(default_factory=make_unique_id_str)
    resource_id: str
    entry: T
    message: str
    cmdtype: Literal["add_entry"] = "add_entry"


class AddEntry(GenericAddEntry[dict]):
    """Command to add an entry."""


class AddEntries(Command):  # noqa: D101
    resource_id: str
    entries: Iterable[dict]
    message: str
    chunk_size: int = 0


class AddEntriesInChunks(AddEntries):  # noqa: D101
    chunk_size: int


class DeleteEntry(Command):  # noqa: D101
    resource_id: str
    entity_id: UniqueIdStr
    version: int
    message: Optional[str] = None
    cmdtype: Literal["delete_entry"] = "delete_entry"


class ImportEntries(AddEntries):  # noqa: D101
    pass


class ImportEntriesInChunks(AddEntriesInChunks):  # noqa: D101
    pass


class GenericUpdateEntry(GenericModel, Generic[T], Command):  # noqa: D101
    resource_id: str
    entity_id: UniqueIdStr
    version: int
    entry: T
    message: str
    force: bool = False
    cmdtype: Literal["update_entry"] = "update_entry"


class UpdateEntry(GenericUpdateEntry[dict]):  # noqa: D101
    ...
