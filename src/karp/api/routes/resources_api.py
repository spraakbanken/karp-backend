import logging
import typing

import pydantic
from fastapi import (
    APIRouter,
    Depends,
    Query,
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


config_description = """
Configuration for resources. Only returns resources with `protected_metadata == true` if the user is authenticated and
has READ access to resource.

By default, returns only resources with unprotected metadata. Use the flags `include_protected_metadata` and 
`include_unprotected_metadata` to include/exclude protected/unprotected metadata.
"""


class FieldConfigResponse(BaseModel):
    # See Field in resource_config.py for more comments about these fields

    model_config = pydantic.ConfigDict(title="Field configuration")

    type: str = pydantic.Field(description="Type of field: text, int, bool or object. Objects have fields.")
    required: bool = pydantic.Field(False, description="If true, a value will always be available for this field.")
    collection: bool = pydantic.Field(False, description="If true, the value will be an array.")
    virtual: bool = pydantic.Field(
        False,
        description="If true, the field can be included in entries returned by `/query`, but cannot be used when editing.",
    )
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
    protected: bool = pydantic.Field(
        False,
        description="If true, the entries are only available for authenticated users with access.",
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
        if isinstance(config.sort, str):
            sort = config.sort
        elif isinstance(config.sort, list) and len(config.sort) == 1:
            sort = config.sort[0]
        else:
            logger.warning("Check sort config for resource {config.resource_id}")
            sort = None
        return ResourceConfigResponse(
            resource_id=config.resource_id,
            resource_name={"swe": config.resource_name} if config.resource_name else None,
            fields=FieldConfigResponse.from_field_config(config.fields),
            sort=sort,
            protected=config.protected.get("read", False),
            protected_metadata=config.protected_metadata,
            id=config.id,
        )


@router.get(
    "",
    response_model=typing.List[ResourceConfigResponse],
    response_model_exclude_defaults=True,
    description=config_description,
)
def get_config(
    user: auth.User = Depends(deps.get_user_optional),
    include_protected_metadata: bool = Query(
        False,
        title="include protected metadata",
        description="Include/exclude resources with protected metadata. Only returns data for authenticated users which access.",
    ),
    include_open_metadata: bool = Query(
        True,
        title="include open metadata",
        description="Include/exclude resources with open metadata.",
    ),
):
    resources = resource_repository.get_published_resources()
    res = []
    for resource in resources:
        if (
            # protected_metadata - check if user has access to the configuration of this resource
            resource.config.protected_metadata
            and include_protected_metadata
            and resource_permissions.has_permission(PermissionLevel.read, user, [resource.resource_id])
        ) or (
            # resource does not have protected metadata and is requested
            not resource.config.protected_metadata and include_open_metadata
        ):
            transformed_config = transform_config(resource.config)
            res.append(ResourceConfigResponse.from_resource_config(transformed_config))
    return res
