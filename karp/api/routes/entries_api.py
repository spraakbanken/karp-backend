import logging
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
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


@router.get("/{resource_id}/{entry_id}", summary="Get entry", tags=["History"])
@router.get("/{resource_id}/{entry_id}/{version}", summary="Get entry history", tags=["History"])
def get_history_for_entry(
    resource_id: str,
    entry_id: UniqueIdStr,
    version: Optional[int] = Query(None),
    user: auth.User = Depends(deps.get_user_optional),
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permissions),
    entry_queries: EntryQueries = Depends(deps.get_entry_queries),
    published_resources: List[str] = Depends(deps.get_published_resources),
) -> EntryDto:
    if not resource_permissions.has_permission(auth.PermissionLevel.write, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    if resource_id not in published_resources:
        raise ResourceNotFound(resource_id)
    logger.debug(
        "getting history for entry", extra={"resource_id": resource_id, "entry_id": entry_id}
    )
    return entry_queries.get_entry_history(resource_id, entry_id, version=version)


@router.put(
    "/{resource_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.EntryAddResponse,
    tags=["Editing"],
)
def add_entry(
    resource_id: str,
    data: schemas.EntryAdd,
    user: User = Depends(deps.get_user),
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permissions),
    entry_commands: EntryCommands = Depends(inject_from_req(EntryCommands)),
    published_resources: List[str] = Depends(deps.get_published_resources),
):
    if not resource_permissions.has_permission(PermissionLevel.write, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    if resource_id not in published_resources:
        raise ResourceNotFound(resource_id)
    logger.info("adding entry", extra={"resource_id": resource_id, "data": data})
    try:
        new_entry = entry_commands.add_entry(
            resource_id=resource_id,
            user=user.identifier,
            message=data.message,
            entry=data.entry,
        )
    except errors.IntegrityError as exc:
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
                "error": str(exc),
                "errorCode": karp_errors.ClientErrorCodes.ENTRY_NOT_VALID,
            },
        )

    return {"newID": new_entry.id}


@router.post(
    "/{resource_id}/{entry_id}",
    response_model=schemas.EntryAddResponse,
    tags=["Editing"],
)
def update_entry(
    resource_id: str,
    entry_id: UniqueId,
    data: schemas.EntryUpdate,
    user: User = Depends(deps.get_user),
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permissions),
    entry_commands: EntryCommands = Depends(inject_from_req(EntryCommands)),
    published_resources: List[str] = Depends(deps.get_published_resources),
):
    if not resource_permissions.has_permission(PermissionLevel.write, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    if resource_id not in published_resources:
        raise ResourceNotFound(resource_id)

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
        return responses.JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=err.error_obj
        )
    except Exception as err:
        logger.exception(
            "error occured",
            extra={"resource_id": resource_id, "entry_id": entry_id.str, "data": data},
        )
        raise


@router.delete(
    "/{resource_id}/{entry_id}/{version}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Editing"],
)
def delete_entry(
    resource_id: str,
    entry_id: UniqueId,
    version: int,
    user: User = Depends(deps.get_user),
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permissions),
    entry_commands: EntryCommands = Depends(inject_from_req(EntryCommands)),
    published_resources: List[str] = Depends(deps.get_published_resources),
):
    """Delete a entry from a resource."""
    if not resource_permissions.has_permission(PermissionLevel.write, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    if resource_id not in published_resources:
        raise ResourceNotFound(resource_id)
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
