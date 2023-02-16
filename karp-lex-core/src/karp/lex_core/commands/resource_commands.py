"""Commands for lex resources."""

from typing import Generic, Literal, Optional, TypeVar

import pydantic
from karp.lex_core.value_objects import unique_id
from pydantic.generics import GenericModel

from .base import Command

T = TypeVar("T")


class EntityOrResourceIdMixin(Command):  # noqa: D101
    resource_id: Optional[str]
    entity_id: Optional[unique_id.UniqueIdStr]

    @pydantic.root_validator(pre=True)
    def resource_or_entity_id(cls, values) -> dict:  # noqa: D102, ANN001
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


class GenericCreateResource(GenericModel, Generic[T], Command):  # noqa: D101
    entity_id: unique_id.UniqueIdStr = pydantic.Field(
        default_factory=unique_id.make_unique_id_str
    )
    resource_id: str
    name: str
    config: T
    entry_repo_id: unique_id.UniqueIdStr
    cmdtype: Literal["create_resource"] = "create_resource"


class CreateResource(GenericCreateResource[dict]):
    """Command to create a resource."""

    @classmethod
    def from_dict(  # noqa: D102
        cls,
        data: dict,
        entry_repo_id: unique_id.UniqueIdPrimitive,
        user: Optional[str] = None,
        message: Optional[str] = None,
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


class GenericUpdateResource(EntityOrResourceIdMixin, GenericModel, Generic[T], Command):
    """Generic command for updating a resource."""

    version: int
    name: str
    config: T
    cmdtype: Literal["update_resource"] = "update_resource"


class UpdateResource(GenericUpdateResource[dict]):
    """Command for updating a resource."""


class PublishResource(EntityOrResourceIdMixin, Command):  # noqa: D101
    version: int
    cmdtype: Literal["publish_resource"] = "publish_resource"


class DeleteResource(EntityOrResourceIdMixin, Command):  # noqa: D101
    version: int
    cmdtype: Literal["delete_resource"] = "delete_resource"


class SetEntryRepoId(EntityOrResourceIdMixin, Command):  # noqa: D101
    entry_repo_id: unique_id.UniqueIdStr
    version: int
    cmdtype: Literal["set_entry_repo_id"] = "set_entry_repo_id"
