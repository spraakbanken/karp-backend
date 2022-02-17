import typing

import pydantic

from karp.foundation.value_objects import unique_id
from karp.utility import time

from karp.lex.domain import errors
from .base import Command


class CreateResource(Command):
    entity_id: unique_id.UniqueId = pydantic.Field(
        default_factory=unique_id.make_unique_id)
    resource_id: str
    name: str
    config: typing.Dict
    message: str
    user: str
    entry_repo_id: unique_id.UniqueId

    @classmethod
    def from_dict(
        cls,
        data: typing.Dict,
        entry_repo_id: unique_id.UniqueId,
        user: typing.Optional[str] = None,
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
            entry_repo_id=entry_repo_id,
            user=user or "Unknown user",
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
