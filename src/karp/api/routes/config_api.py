import logging
import typing

import pydantic
from fastapi import (
    APIRouter,
    Depends,
)

from karp import auth
from karp.api import dependencies as deps
from karp.api.schemas import BaseModel
from karp.auth.application import resource_permission_queries as resource_permissions
from karp.foundation.value_objects import PermissionLevel
from karp.lex import Field, ResourceConfig
from karp.lex.infrastructure.sql import resource_repository
from karp.plugins import transform_config

logger = logging.getLogger(__name__)


router = APIRouter()


class FieldConfigResponse(BaseModel):
    # See Field in resource_config.py for more comments about these fields

    model_config = pydantic.ConfigDict(title="Field configuration")

    type: str = pydantic.Field(description="Type of field: text, int, bool or object. Objects have fields.")
    required: bool = pydantic.Field(False, description="If true, a value will always be available for this field.")
    collection: bool = pydantic.Field(False, description="If true, the value will be an array.")
    virtual: bool = pydantic.Field(False, description="If true, the field cannot be used when editing.")
    fields: dict[str, "FieldConfigResponse"] | None = pydantic.Field(
        None, description="When type == 'object', the inner fields are given here (recursive type)."
    )
    searchable: bool = pydantic.Field(
        True, description="If false, the field cannot be used in queries. Only used for virtual fields."
    )
    label: dict[str, str] | None = pydantic.Field(
        None, description="An object containing labels. The keys are language codes."
    )

    def from_field_config(fields: dict[str, Field]) -> dict[str, typing.Self]:
        res = {}
        for key, field in fields.items():
            if not field.store:
                # in theory a field could be searchable but not stored
                # but for now, just let API users ignore un-stored fields
                continue
            res[key] = FieldConfigResponse(
                type=field.type,
                required=field.required,
                collection=field.collection,
                virtual=field.virtual,
                searchable=field.searchable,
            )
            if field.type == "object":
                res[key].fields = FieldConfigResponse.from_field_config(field.fields)
        return res


class ResourceConfigResponse(BaseModel):
    resource_id: str = pydantic.Field(title="Resource ID", description="A unique identifier for this resource.")
    resource_name: dict[str, str] | None = pydantic.Field(
        None, title="Resource name", description="An object containing labels. The keys are language codes."
    )
    fields: dict[str, FieldConfigResponse] = pydantic.Field(
        description="A description of all fields in this resource. The keys are the field names."
    )
    sort: str | None = pydantic.Field(None, description="Results will be sorted by this field by default.")
    protected: dict[str, bool] = pydantic.Field(
        default_factory=dict,
        description="If `{read: true}`, the entries are only available for authenticated users with access.",
    )
    protected_metadata: bool = pydantic.Field(
        False,
        title="Protected metadata",
        description="If true, the configuration is only available for authenticated users with access.",
    )
    id: str | None = pydantic.Field(
        None, title="ID", description="The field used as an identifier for entries in this resource."
    )

    def from_resource_config(config: ResourceConfig) -> typing.Self:
        return ResourceConfigResponse(
            resource_id=config.resource_id,
            resource_name={"swe": config.resource_name} if config.resource_name else None,
            fields=FieldConfigResponse.from_field_config(config.fields),
            sort=config.sort,
            protected=config.protected,
            protected_metadata=config.protected_metadata,
            id=config.id,
        )


@router.get(
    "",
    response_model=typing.List[ResourceConfigResponse],
    response_model_exclude_defaults=True,
    description="""
    Configuration for resources. Returns all resources except those with `protected_metadata == true`.
    
    If `protected_metadata == true`", the configuration is only returned when a user is authenticated and has access.
    """,
)
def get_config(
    user: auth.User = Depends(deps.get_user_optional),
):
    resources = resource_repository.get_published_resources()
    res = []
    for resource in resources:
        if resource.config.protected_metadata and not resource_permissions.has_permission(
            PermissionLevel.read, user, [resource.resource_id]
        ):
            # user does not have access to the configuration of this resource
            continue
        transformed_config = transform_config(resource.config)
        res.append(ResourceConfigResponse.from_resource_config(transformed_config))
    return res
