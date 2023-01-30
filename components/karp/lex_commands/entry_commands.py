import typing

import pydantic

from karp.foundation.value_objects import unique_id
from .base import Command
from karp.utility import time

from karp.lex.domain import errors
from karp.lex.domain.value_objects import UniqueId


class AddEntry(Command):
    entity_id: unique_id.UniqueId = pydantic.Field(
        default_factory=unique_id.make_unique_id
    )
    resource_id: str
    entry: typing.Dict
    user: str
    message: str


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
    entity_id: UniqueId
    user: str
    message: typing.Optional[str] = None


class ImportEntries(AddEntries):
    pass


class ImportEntriesInChunks(AddEntriesInChunks):
    pass


class UpdateEntry(Command):
    resource_id: str
    entity_id: UniqueId
    # entry_id: str
    version: int
    entry: typing.Dict
    user: str
    message: str
    resource_version: typing.Optional[int] = None
    force: bool = False
