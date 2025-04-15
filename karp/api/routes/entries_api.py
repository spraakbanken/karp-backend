import logging
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from starlette import responses

from karp import auth
from karp.api import dependencies as deps
from karp.api import schemas
from karp.api.dependencies.fastapi_injector import inject_from_req
from karp.auth import User
from karp.auth.application import ResourcePermissionQueries
from karp.entry_commands import EntryCommands
from karp.foundation.value_objects import PermissionLevel, UniqueId, unique_id
from karp.foundation.value_objects.unique_id import UniqueIdStr
from karp.lex import EntryDto
from karp.lex.application import EntryQueries
from karp.lex.domain import errors
from karp.lex.domain.errors import ResourceNotFound
from karp.main import errors as karp_errors

router = APIRouter()

logger = logging.getLogger(__name__)

# add, update and delete can result in these errors (but not all error codes)
crud_responses: dict[int | str, dict[str, str]] = {
    400: {
        "description": """
### Error codes
- 30: Entry not found
- 32: Entry not valid
- 33: Version conflict
- 61: Database integrity error
"""
    },
    403: {"description": "User does not have write access to resource"},
    404: {"description": "Resource do not exist"},
}

# /entries/<resources>/<entry_id> can have 404 and 403 but not 400 with error code
history_responses: dict[int | str, dict[str, str]] = {key: val for key, val in crud_responses.items() if key != 400}


@router.get("/{resource_id}/{entry_id}", summary="Get entry", tags=["History"], responses=history_responses)
@router.get(
    "/{resource_id}/{entry_id}/{version}", summary="Get entry history", tags=["History"], responses=history_responses
)
def get_history_for_entry(
    resource_id: str,
    entry_id: UniqueIdStr,
    version: Optional[int] = None,
    user: auth.User = Depends(deps.get_user_optional),
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permission_queries),
    entry_queries: EntryQueries = Depends(deps.get_entry_queries),
    published_resources: List[str] = Depends(deps.get_published_resources),
) -> EntryDto:
    if resource_id not in published_resources:
        raise ResourceNotFound(resource_id)
    if not resource_permissions.has_permission(auth.PermissionLevel.write, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    logger.debug("getting history for entry", extra={"resource_id": resource_id, "entry_id": entry_id})
    return entry_queries.get_entry_history(resource_id, entry_id, version=version)


@router.get(
    "/create_id",
    status_code=status.HTTP_200_OK,
    tags=["Editing"],
    description="""
    Create an ID (ULID) to be used as input for `add/<resource_id>/<entry_id>`. 
    """,
)
def create_id() -> schemas.EntryAddResponse:
    return schemas.EntryAddResponse(newID=unique_id.make_unique_id().str)


@router.put(
    "/{resource_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.EntryAddResponse,
    tags=["Editing"],
    deprecated=True,
    description="Deprecated, use `add/<resource_id>/<entry_id>` instead.",
)
def add_entry(
    resource_id: str,
    data: schemas.EntryAdd,
    user: User = Depends(deps.get_user),
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permission_queries),
    entry_commands: EntryCommands = Depends(inject_from_req(EntryCommands)),
    entry_queries: EntryQueries = Depends(deps.get_entry_queries),
    published_resources: List[str] = Depends(deps.get_published_resources),
):
    entry_id = unique_id.make_unique_id()
    return add_entry_with_id(
        resource_id, entry_id, data, user, resource_permissions, entry_commands, entry_queries, published_resources
    )


@router.put(
    "/{resource_id}/{entry_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.EntryAddResponse,
    tags=["Editing"],
    description="""
    Add a new entry. For data consistency reasons, first generate an ID (ULID), for example using the `create_id` API 
    call. If the request fails, use the same ID to try again, this ensures that the entry body is not added several 
    times. Answers:
    
- `201 Created` if the entry exists with the same body, at version 1
- `400` 
    - if the `entry_id` exists, but the body is different
    - if the `entry_id`  is not valid
    - if the entry is not valid according to resource settings
    """,
    responses=crud_responses,
)
def add_entry_with_id(
    resource_id: str,
    entry_id: UniqueIdStr,
    data: schemas.EntryAdd,
    user: User = Depends(deps.get_user),
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permission_queries),
    entry_commands: EntryCommands = Depends(inject_from_req(EntryCommands)),
    entry_queries: EntryQueries = Depends(deps.get_entry_queries),
    published_resources: List[str] = Depends(deps.get_published_resources),
):
    if resource_id not in published_resources:
        raise ResourceNotFound(resource_id)
    if not resource_permissions.has_permission(PermissionLevel.write, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    logger.info("adding entry", extra={"resource_id": resource_id, "data": data})
    try:
        entry_commands.add_entry(
            resource_id=resource_id,
            entry_id=entry_id,
            user=user.identifier,
            message=data.message,
            entry=data.entry,
        )
    except errors.IntegrityError as exc:
        existing_entry = entry_queries.by_id_optional(resource_id, entry_id, expand_plugins=False)
        if not existing_entry or existing_entry.version != 1 or existing_entry.entry != data.entry:
            return responses.JSONResponse(
                status_code=400,
                content={
                    "error": str(exc),
                    "errorCode": karp_errors.ClientErrorCodes.DB_INTEGRITY_ERROR,
                },
            )
    except errors.InvalidEntry as exc:
        return responses.JSONResponse(
            status_code=400,
            content={
                "error": exc.extras["reason"],
                "errorCode": karp_errors.ClientErrorCodes.ENTRY_NOT_VALID,
            },
        )

    return schemas.EntryAddResponse(newID=entry_id)


# must go before update_entry otherwise it thinks this is an
# update requests with entry_id="preview"
@router.post(
    "/{resource_id}/preview",
    response_model=schemas.EntryPreviewResponse,
    tags=["Editing"],
    responses=crud_responses,
)
def preview_entry(
    resource_id: str,
    data: schemas.EntryPreview,
    user: User = Depends(deps.get_user),
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permission_queries),
    entry_queries: EntryQueries = Depends(inject_from_req(EntryQueries)),
    published_resources: List[str] = Depends(deps.get_published_resources),
    responses=crud_responses,
):
    if resource_id not in published_resources:
        raise ResourceNotFound(resource_id)
    if not resource_permissions.has_permission(PermissionLevel.read, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    logger.info(
        "previewing entry",
        extra={
            "resource_id": resource_id,
            "data": data,
            "user": user.identifier,
        },
    )

    result = entry_queries.transform_entry_body(resource_id, data.entry)
    return schemas.EntryPreviewResponse(entry=result)


@router.post(
    "/{resource_id}/{entry_id}",
    response_model=schemas.EntryAddResponse,
    tags=["Editing"],
    responses=crud_responses,
)
def update_entry(
    resource_id: str,
    entry_id: UniqueId,
    data: schemas.EntryUpdate,
    user: User = Depends(deps.get_user),
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permission_queries),
    entry_commands: EntryCommands = Depends(inject_from_req(EntryCommands)),
    published_resources: List[str] = Depends(deps.get_published_resources),
):
    if resource_id not in published_resources:
        raise ResourceNotFound(resource_id)
    if not resource_permissions.has_permission(PermissionLevel.write, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    logger.info(
        "updating entry",
        extra={
            "resource_id": resource_id,
            "entry_id": entry_id,
            "data": data,
            "user": user.identifier,
        },
    )
    try:
        entry = entry_commands.update_entry(
            resource_id=resource_id,
            _id=unique_id.parse(entry_id),
            version=data.version,
            user=user.identifier,
            message=data.message,
            entry=data.entry,
        )

        return schemas.EntryAddResponse(newID=entry.id)

    except errors.EntryNotFound:
        return responses.JSONResponse(
            status_code=404,
            content={
                "error": f"Entry '{entry_id}' not found in resource '{resource_id}' (version=latest)",
                "errorCode": karp_errors.ClientErrorCodes.ENTRY_NOT_FOUND,
                "resource": resource_id,
                "entry_id": entry_id.str,
            },
        )
    except errors.UpdateConflict as err:
        err.error_obj["errorCode"] = karp_errors.ClientErrorCodes.VERSION_CONFLICT
        return responses.JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=err.error_obj)
    except errors.InvalidEntry as exc:
        return responses.JSONResponse(
            status_code=400,
            content={
                "error": exc.extras["reason"],
                "errorCode": karp_errors.ClientErrorCodes.ENTRY_NOT_VALID,
            },
        )
    except Exception:
        logger.exception(
            "error occured",
            extra={"resource_id": resource_id, "entry_id": entry_id.str, "data": data},
        )
        raise


@router.delete(
    "/{resource_id}/{entry_id}/{version}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Editing"],
    responses=crud_responses,
)
def delete_entry(
    resource_id: str,
    entry_id: UniqueId,
    version: int,
    user: User = Depends(deps.get_user),
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permission_queries),
    entry_commands: EntryCommands = Depends(inject_from_req(EntryCommands)),
    published_resources: List[str] = Depends(deps.get_published_resources),
):
    """Delete a entry from a resource."""
    if resource_id not in published_resources:
        raise ResourceNotFound(resource_id)
    if not resource_permissions.has_permission(PermissionLevel.write, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    try:
        entry_commands.delete_entry(
            resource_id=resource_id,
            _id=unique_id.parse(entry_id),
            user=user.identifier,
            version=version,
        )
    except errors.EntryNotFound:
        return responses.JSONResponse(
            status_code=404,
            content={
                "error": f"Entry '{entry_id}' not found in resource '{resource_id}' (version=latest)",
                "errorCode": karp_errors.ClientErrorCodes.ENTRY_NOT_FOUND,
                "resource": resource_id,
                "id": entry_id.str,
            },
        )
    return
