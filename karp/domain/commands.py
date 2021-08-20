import typing

import pydantic

from . import errors
from karp.utility import time, unique_id

# pylint: disable=unsubscriptable-object


class Command(pydantic.BaseModel):  # pylint: disable=no-member
    timestamp: float = pydantic.Field(default_factory=time.utc_now)


# Resource commands


class CreateResource(Command):
    id: unique_id.UniqueId = pydantic.Field(default_factory=unique_id.make_unique_id)
    resource_id: str
    name: str
    config: typing.Dict
    message: str
    created_by: str
    entry_repository_type: typing.Optional[str] = None
    entry_repository_settings: typing.Optional[typing.Dict] = None

    @classmethod
    def from_dict(
        cls,
        data: typing.Dict,
        created_by: typing.Optional[str] = None,
        message: typing.Optional[str] = None,
    ):
        try:
            resource_id = data.pop("resource_id")
        except KeyError:
            raise errors.ConstraintsError("'resource_id' is missing")
        try:
            name = data.pop("resource_name")
        except KeyError:
            raise errors.ConstraintsError("'resource_name' is missing")

        return cls(
            resource_id=resource_id,
            name=name,
            config=data,
            created_by=created_by or "Unknown user",
            message=message or f"Resource '{resource_id}' created.",
        )


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


class ReindexResource(Command):
    resource_id: str


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
    # ids: typing.Iterable[unique_id.UniqueId]
    entries: typing.Iterable[typing.Dict]
    user: str
    message: str


class DeleteEntry(Command):
    resource_id: str
    entry_id: str
    user: str
    message: typing.Optional[str] = None


class UpdateEntry(Command):
    resource_id: str
    entry_id: str
    version: int
    entry: typing.Dict
    user: str
    message: str
    resource_version: typing.Optional[int] = None
    force: bool = False
