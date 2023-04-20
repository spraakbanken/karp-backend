"""Commands for lex resources."""

from typing import Generic, Literal, Optional, TypeVar

import pydantic
from karp.lex_core.value_objects.unique_id import (
    UniqueId,
    UniqueIdPrimitive,
    make_unique_id,
)
from pydantic.generics import GenericModel

from .base import Command

T = TypeVar("T")


class EntityOrResourceIdMixin(Command):  # noqa: D101
    resource_id: Optional[str]
    id: Optional[UniqueId]  # noqa: A003

    @pydantic.root_validator(pre=True)
    def resource_id_or_id(cls, values) -> dict:  # noqa: D102, ANN001
        resource_id = values["resourceId"] if "resourceId" in values else None
        if "id" in values and resource_id:
            raise ValueError("Can't give both 'id' and 'resourceId'")

        if resource_id:
            return dict(values) | {
                "id": None,
                "resourceId": resource_id,
            }
        elif "id" in values:
            return dict(values) | {
                "resourceId": None,
            }
        else:
            raise ValueError("Must give either 'id' or 'resourceId'")


class GenericCreateResource(GenericModel, Generic[T], Command):  # noqa: D101
    id: UniqueId = pydantic.Field(default_factory=make_unique_id)  # noqa: A003
    resource_id: str
    name: str
    config: T
    entry_repo_id: UniqueId
    cmdtype: Literal["create_resource"] = "create_resource"


class CreateResource(GenericCreateResource[dict]):
    """Command to create a resource."""

    @classmethod
    def from_dict(  # noqa: D102
        cls,
        data: dict,
        entry_repo_id: UniqueIdPrimitive,
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

        return cls(
            resourceId=resource_id,
            name=name,
            config=data,
            entryRepoId=entry_repo_id,
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
    #    version: int
    cmdtype: Literal["delete_resource"] = "delete_resource"


class SetEntryRepoId(EntityOrResourceIdMixin, Command):  # noqa: D101
    entry_repo_id: UniqueId
    version: int
    cmdtype: Literal["set_entry_repo_id"] = "set_entry_repo_id"
