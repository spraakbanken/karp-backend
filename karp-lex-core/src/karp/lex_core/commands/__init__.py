"""Commands top-level module."""

from typing import Union

from pydantic import BaseModel, Field

from .entry_commands import (
    AddEntries,
    AddEntriesInChunks,
    AddEntry,
    DeleteEntry,
    GenericAddEntry,
    GenericUpdateEntry,
    ImportEntries,
    ImportEntriesInChunks,
    UpdateEntry,
)
from .entry_repo_commands import CreateEntryRepository, DeleteEntryRepository
from .resource_commands import (
    CreateResource,
    DeleteResource,
    GenericCreateResource,
    GenericUpdateResource,
    PublishResource,
    SetEntryRepoId,
    UpdateResource,
)

__all__ = [
    # Entry commands
    "AddEntries",
    "AddEntriesInChunks",
    "AddEntry",
    "DeleteEntry",
    "GenericAddEntry",
    "GenericUpdateEntry",
    "ImportEntries",
    "ImportEntriesInChunks",
    "UpdateEntry",
    # EntryRepo commands
    "CreateEntryRepository",
    "DeleteEntryRepository",
    # Resource commands
    "CreateResource",
    "DeleteResource",
    "GenericCreateResource",
    "GenericUpdateResource",
    "PublishResource",
    "SetEntryRepoId",
    "UpdateResource",
]


EntryCommandType = Union[AddEntry, DeleteEntry, UpdateEntry]


EntryRepoCommandType = Union[CreateEntryRepository, DeleteEntryRepository]
ResourceCommandType = Union[
    CreateResource, DeleteResource, PublishResource, SetEntryRepoId, UpdateResource
]


class LexCommand(BaseModel):  # noqa: D101
    command: Union[EntryCommandType, EntryRepoCommandType, ResourceCommandType] = Field(
        ..., discriminator="cmdtype"
    )


class EntryCommand(BaseModel):  # noqa: D101
    command: EntryCommandType = Field(..., discriminator="cmdtype")


class EntryRepoCommand(BaseModel):  # noqa: D101
    command: EntryRepoCommandType = Field(..., discriminator="cmdtype")


class ResourceCommand(BaseModel):  # noqa: D101
    command: ResourceCommandType = Field(..., discriminator="cmdtype")
