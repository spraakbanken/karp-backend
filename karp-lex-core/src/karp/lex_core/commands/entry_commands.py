import typing

import pydantic
from karp.lex_core.value_objects import UniqueIdStr, make_unique_id_str

from .base import Command


class AddEntry(Command):
    entity_id: UniqueIdStr = pydantic.Field(default_factory=make_unique_id_str)
    resource_id: str
    entry: typing.Dict
    user: str
    message: str
    cmdtype: typing.Literal["add_entry"] = "add_entry"


class AddEntries(Command):
    resource_id: str
    entries: typing.Iterable[typing.Dict]
    user: str
    message: str
    chunk_size: int = 0


class AddEntriesInChunks(AddEntries):
    chunk_size: int


class DeleteEntry(Command):
    resource_id: str
    entity_id: UniqueIdStr
    version: int
    user: str
    message: typing.Optional[str] = None
    cmdtype: typing.Literal["delete_entry"] = "delete_entry"


class ImportEntries(AddEntries):
    pass


class ImportEntriesInChunks(AddEntriesInChunks):
    pass


class UpdateEntry(Command):
    resource_id: str
    entity_id: UniqueIdStr
    # entry_id: str
    version: int
    entry: typing.Dict
    user: str
    message: str
    resource_version: typing.Optional[int] = None
    force: bool = False
    cmdtype: typing.Literal["update_entry"] = "update_entry"
