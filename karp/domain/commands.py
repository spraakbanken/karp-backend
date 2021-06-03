import typing

import pydantic

from karp.utility import time, unique_id

# pylint: disable=unsubscriptable-object


class Command(pydantic.BaseModel):  # pylint: disable=no-member
    timestamp: float = pydantic.Field(default_factory=time.utc_now)


# Resource commands


class CreateResource(Command):
    id: unique_id.UniqueId
    resource_id: str
    name: str
    config: typing.Dict
    message: str
    created_by: str
    entry_repository_type: typing.Optional[str] = None
    entry_repository_settings: typing.Optional[typing.Dict] = None


class UpdateResource(Command):
    resource_id: str
    version: int
    name: str
    config: typing.Dict
    message: str
    user: str


class PublishResource(Command):
    resource_id: str
    message: str
    user: str


# Entry commands
class AddEntry(Command):
    resource_id: str
    id: unique_id.UniqueId
    # entry_id: str
    entry: typing.Dict
    user: str
    message: str


class AddEntries(Command):
    resource_id: str
    ids: typing.Iterable[unique_id.UniqueId]
    entries: typing.Iterable[typing.Dict]
    user: str
    message: str


class DeleteEntry(Command):
    resource_id: str
    entry_id: str
    version: int
    user: str
    message: str


class UpdateEntry(Command):
    resource_id: str
    entry_id: str
    version: int
    entry: typing.Dict
    user: str
    message: str
    resource_version: typing.Optional[int] = None
    force: bool = False
