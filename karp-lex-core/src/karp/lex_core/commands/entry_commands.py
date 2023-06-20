from typing import (
    Annotated,
    Generic,
    Iterable,
    Literal,
    Optional,
    TypeVar,
    Union,
)

import pydantic
from karp.lex_core.value_objects import UniqueId, make_unique_id
from pydantic.generics import GenericModel

from .base import Command

T = TypeVar("T")


class GenericAddEntry(GenericModel, Generic[T], Command):  # noqa: D101
    id: UniqueId = pydantic.Field(default_factory=make_unique_id)  # noqa: A003
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
    id: UniqueId  # noqa: A003
    version: int
    message: Optional[str] = None
    cmdtype: Literal["delete_entry"] = "delete_entry"


class ImportEntries(AddEntries):  # noqa: D101
    pass


class ImportEntriesInChunks(AddEntriesInChunks):  # noqa: D101
    pass


class GenericUpdateEntry(GenericModel, Generic[T], Command):  # noqa: D101
    resource_id: str
    id: UniqueId  # noqa: A003
    version: int
    entry: T
    message: str
    force: bool = False
    cmdtype: Literal["update_entry"] = "update_entry"


class UpdateEntry(GenericUpdateEntry[dict]):  # noqa: D101
    ...


EntryCommandType = Annotated[
    Union[AddEntry, DeleteEntry, UpdateEntry], pydantic.Field(discriminator="cmdtype")
]


class EntryCommand(pydantic.BaseModel):
    cmd: EntryCommandType


class ExecuteBatchOfEntryCommands(pydantic.BaseModel):
    commands: Iterable[EntryCommand]
