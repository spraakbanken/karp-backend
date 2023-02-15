"""Commands top-level module."""

from typing import Union

from pydantic import BaseModel, Field

from .entry_commands import (
    AddEntries,
    AddEntriesInChunks,
    AddEntry,
    DeleteEntry,
    ImportEntries,
    ImportEntriesInChunks,
    UpdateEntry,
)
from .entry_repo_commands import CreateEntryRepository, DeleteEntryRepository
from .resource_commands import (
    CreateResource,
    DeleteResource,
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
    "ImportEntries",
    "ImportEntriesInChunks",
    "UpdateEntry",
    # EntryRepo commands
    "CreateEntryRepository",
    "DeleteEntryRepository",
    # Resource commands
    "CreateResource",
    "DeleteResource",
    "PublishResource",
    "SetEntryRepoId",
    "UpdateResource",
]


EntryCommandType = Union[AddEntry, DeleteEntry, UpdateEntry]


EntryRepoCommandType = Union[CreateEntryRepository, DeleteEntryRepository]
ResourceCommandType = Union[
    CreateResource, DeleteResource, PublishResource, SetEntryRepoId, UpdateResource
]


class LexCommand(BaseModel):
    command: Union[EntryCommandType, EntryRepoCommandType, ResourceCommandType] = Field(
        ..., discriminator="cmdtype"
    )


class EntryCommand(BaseModel):
    command: EntryCommandType = Field(..., discriminator="cmdtype")


class EntryRepoCommand(BaseModel):
    command: EntryRepoCommandType = Field(..., discriminator="cmdtype")


class ResourceCommand(BaseModel):
    command: ResourceCommandType = Field(..., discriminator="cmdtype")
