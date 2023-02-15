import typing
from typing import Literal, Optional

import pydantic
from karp.lex_core.value_objects import unique_id

from .base import Command


class EntityOrResourceIdMixin(Command):
    resource_id: Optional[str]
    entity_id: Optional[unique_id.UniqueIdStr]

    @pydantic.root_validator(pre=True)
    def resource_or_entity_id(cls, values) -> dict:
        entity_id = None
        if "entityId" in values:
            entity_id = values["entityId"]

        resource_id = None
        if "resourceId" in values:
            resource_id = values["resourceId"]

        if entity_id and resource_id:
            raise ValueError("Can't give both 'entityId' and 'resourceId'")

        if entity_id is None and resource_id is None:
            raise ValueError("Must give either 'entityId' or 'resourceId'")

        if resource_id:
            return dict(values) | {
                "entityId": None,
                "resourceId": resource_id,
            }

        return dict(values) | {
            "entityId": entity_id,
            "resourceId": None,
        }


class CreateResource(Command):
    entity_id: unique_id.UniqueIdStr = pydantic.Field(
        default_factory=unique_id.make_unique_id_str
    )
    resource_id: str
    name: str
    config: dict
    entry_repo_id: unique_id.UniqueIdStr
    cmdtype: Literal["create_resource"] = "create_resource"

    @classmethod
    def from_dict(
        cls,
        data: dict,
        entry_repo_id: unique_id.UniqueIdPrimitive,
        user: typing.Optional[str] = None,
        message: typing.Optional[str] = None,
    ) -> "CreateResource":
        try:
            resource_id = data.pop("resource_id")
        except KeyError as exc:
            raise ValueError("'resource_id' is missing") from exc
        try:
            name = data.pop("resource_name")
        except KeyError as exc:
            raise ValueError("'resource_name' is missing") from exc

        entry_repo_id = unique_id.parse(entry_repo_id)

        return cls(
            resource_id=resource_id,
            name=name,
            config=data,
            entry_repo_id=entry_repo_id,
            user=user or "Unknown user",
            message=message or f"Resource '{resource_id}' created.",
        )


class UpdateResource(EntityOrResourceIdMixin, Command):
    version: int
    name: str
    config: dict
    cmdtype: Literal["update_resource"] = "update_resource"


class PublishResource(EntityOrResourceIdMixin, Command):
    version: int
    cmdtype: Literal["publish_resource"] = "publish_resource"


class DeleteResource(EntityOrResourceIdMixin, Command):
    version: int
    cmdtype: Literal["delete_resource"] = "delete_resource"


class SetEntryRepoId(EntityOrResourceIdMixin, Command):
    entry_repo_id: unique_id.UniqueIdStr
    version: int
    cmdtype: Literal["set_entry_repo_id"] = "set_entry_repo_id"
