import logging  # noqa: D100, I001
from typing import Optional
import uuid  # noqa: F401

from fastapi import (
    APIRouter,
    Body,  # noqa: F401
    Depends,
    HTTPException,
    Security,
    status,
    Path,  # noqa: F401
    Query,
)
import pydantic
from starlette import responses
from karp.lex_core.value_objects import UniqueId, unique_id
from karp.lex_core.value_objects.unique_id import UniqueIdStr

from karp.main import errors as karp_errors
from karp import auth, search
from karp.lex.application.queries import EntryDto, GetEntryHistory
from karp.lex import commands
from karp.lex.domain import errors
from karp.auth import User
from karp.foundation.value_objects import PermissionLevel
from karp.auth import AuthService
from karp.karp_v6_api import schemas, dependencies as deps
from karp.command_bus import CommandBus


router = APIRouter()

logger = logging.getLogger(__name__)


@router.get(
    "/{resource_id}/{entry_id}/{version}", response_model=EntryDto, tags=["History"]
)
@router.get("/{resource_id}/{entry_id}", response_model=EntryDto, tags=["History"])
def get_history_for_entry(  # noqa: ANN201, D103
    resource_id: str,
    entry_id: UniqueIdStr,
    version: Optional[int] = Query(None),
    user: auth.User = Security(deps.get_user, scopes=["admin"]),
    auth_service: auth.AuthService = Depends(deps.get_auth_service),
    get_entry_history: GetEntryHistory = Depends(deps.get_entry_history),
):
    if not auth_service.authorize(auth.PermissionLevel.admin, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="lexica:admin"'},
        )
    logger.info(
        "getting history for entry",
        extra={
            "resource_id": resource_id,
            "entry_id": entry_id,
            "user": user.identifier,
        },
    )
    return get_entry_history.query(resource_id, entry_id, version=version)


@router.post(
    "/{resource_id}/add",
    status_code=status.HTTP_201_CREATED,
    tags=["Editing"],
    response_model=schemas.EntryAddResponse,
)
@router.put(
    "/{resource_id}",
    status_code=status.HTTP_201_CREATED,
    tags=["Editing"],
    response_model=schemas.EntryAddResponse,
)
def add_entry(  # noqa: ANN201, D103
    resource_id: str,
    data: schemas.EntryAdd,
    user: User = Security(deps.get_user, scopes=["write"]),
    auth_service: AuthService = Depends(deps.get_auth_service),
    command_bus: CommandBus = Depends(deps.inject_from_req(CommandBus)),
):
    if not auth_service.authorize(PermissionLevel.write, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="write"'},
        )
    logger.info("adding entry", extra={"resource_id": resource_id, "data": data})
    try:
        new_entry = command_bus.dispatch(
            commands.AddEntry(
                resourceId=resource_id,
                user=user.identifier,
                message=data.message,
                entry=data.entry,
            )
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


@router.post("/{resource_id}/preview")
def preview_entry(  # noqa: ANN201, D103
    resource_id: str,
    data: schemas.EntryAdd,
    user: auth.User = Security(deps.get_user_optional, scopes=["read"]),
    auth_service: auth.AuthService = Depends(deps.get_auth_service),
    preview_entry: search.PreviewEntry = Depends(
        deps.inject_from_req(search.PreviewEntry)
    ),
):
    if not auth_service.authorize(PermissionLevel.read, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="lexica:read"'},
        )
    try:
        input_dto = search.PreviewEntryInputDto(
            resourceId=resource_id, entry=data.entry, user=user.identifier
        )
    except pydantic.ValidationError as err:
        logger.exception("data is not valid")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail={"error": str(err)}
        ) from err
    else:
        return preview_entry.query(input_dto)


@router.post(
    "/{resource_id}/{entry_id}/update",
    tags=["Editing"],
    response_model=schemas.EntryAddResponse,
)
@router.post(
    "/{resource_id}/{entry_id}",
    tags=["Editing"],
    response_model=schemas.EntryAddResponse,
)
def update_entry(  # noqa: ANN201, D103
    resource_id: str,
    entry_id: UniqueId,
    data: schemas.EntryUpdate,
    user: User = Security(deps.get_user, scopes=["write"]),
    auth_service: AuthService = Depends(deps.get_auth_service),
    command_bus: CommandBus = Depends(deps.inject_from_req(CommandBus)),
):
    if not auth_service.authorize(PermissionLevel.write, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="write"'},
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
        entry = command_bus.dispatch(
            commands.UpdateEntry(
                resourceId=resource_id,
                id=unique_id.parse(entry_id),
                version=data.version,
                user=user.identifier,
                message=data.message,
                entry=data.entry,
            )
        )

        return schemas.EntryAddResponse(newID=entry.entity_id)

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
    except Exception as err:  # noqa: F841
        logger.exception(
            "error occured",
            extra={"resource_id": resource_id, "entry_id": entry_id.str, "data": data},
        )
        raise


@router.delete(
    "/{resource_id}/{entry_id}/{version}/delete",
    tags=["Editing"],
    status_code=status.HTTP_204_NO_CONTENT,
)
@router.delete(
    "/{resource_id}/{entry_id}/{version}",
    tags=["Editing"],
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_entry(  # noqa: ANN201
    resource_id: str,
    entry_id: UniqueId,
    version: int,
    user: User = Security(deps.get_user, scopes=["write"]),
    auth_service: AuthService = Depends(deps.get_auth_service),
    command_bus: CommandBus = Depends(deps.inject_from_req(CommandBus)),
):
    """Delete a entry from a resource."""
    if not auth_service.authorize(PermissionLevel.write, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="lexica:write"'},
        )
    try:
        command_bus.dispatch(
            commands.DeleteEntry(
                resourceId=resource_id,
                id=unique_id.parse(entry_id),
                user=user.identifier,
                version=version,
            )
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


def init_app(app):  # noqa: ANN201, D103
    app.include_router(router)
