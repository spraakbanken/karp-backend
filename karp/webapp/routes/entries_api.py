import logging
from typing import Optional
import uuid

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Response,
    Security,
    status,
    Path,
    Query,
)
import pydantic
from starlette import responses
from karp.foundation.value_objects import unique_id
from karp.foundation.value_objects.unique_id import UniqueIdStr

from karp.lex.domain.value_objects import UniqueId
from karp import errors as karp_errors, auth, lex, search
from karp.lex.application.queries import EntryDto, GetEntryHistory
from karp.lex.domain import commands, errors
from karp.auth import User
from karp.foundation.value_objects import PermissionLevel
from karp.auth import AuthService
from karp.webapp import schemas, dependencies as deps


router = APIRouter()

logger = logging.getLogger(__name__)


@router.get(
    "/{resource_id}/{entry_id}/{version}", response_model=EntryDto, tags=["History"]
)
@router.get("/{resource_id}/{entry_id}", response_model=EntryDto, tags=["History"])
def get_history_for_entry(
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
def add_entry(
    resource_id: str,
    data: schemas.EntryAdd,
    user: User = Security(deps.get_user, scopes=["write"]),
    auth_service: AuthService = Depends(deps.get_auth_service),
    adding_entry_uc: lex.AddingEntry = Depends(deps.get_lex_uc(lex.AddingEntry)),
):

    if not auth_service.authorize(PermissionLevel.write, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="write"'},
        )
    logger.info("adding entry", extra={"resource_id": resource_id, "data": data})
    try:
        new_entry = adding_entry_uc.execute(
            commands.AddEntry(
                resource_id=resource_id,
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

    return {"newID": new_entry.entity_id}


@router.post("/{resource_id}/preview")
def preview_entry(
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
            resource_id=resource_id, entry=data.entry, user=user.identifier
        )
    except pydantic.ValidationError as err:
        logger.exception("data is not valid")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail={"error": str(err)}
        )
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
def update_entry(
    response: Response,
    resource_id: str,
    entry_id: UniqueIdStr,
    data: schemas.EntryUpdate,
    user: User = Security(deps.get_user, scopes=["write"]),
    auth_service: AuthService = Depends(deps.get_auth_service),
    updating_entry_uc: lex.UpdatingEntry = Depends(deps.get_lex_uc(lex.UpdatingEntry)),
):
    if not auth_service.authorize(PermissionLevel.write, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="write"'},
        )

    #     force_update = convert.str2bool(request.args.get("force", "false"))
    #     data = request.get_json()
    #     version = data.get("version")
    #     entry = data.get("entry")
    #     message = data.get("message")
    #     if not (version and entry and message):
    #         raise KarpError("Missing version, entry or message")
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
        entry = updating_entry_uc.execute(
            commands.UpdateEntry(
                resource_id=resource_id,
                entity_id=unique_id.parse(entry_id),
                version=data.version,
                user=user.identifier,
                message=data.message,
                entry=data.entry,
            )
        )
        # new_entry = entries.add_entry(
        #     resource_id, data.entry, user.identifier, message=data.message
        # )
        # new_id = entries.update_entry(
        #     resource_id,
        #     entry_id,
        #     data.version,
        #     data.entry,
        #     user.identifier,
        #     message=data.message,
        #     # force=force_update,
        # )
        return {"newID": entry.entity_id}
    except errors.EntryNotFound:
        return responses.JSONResponse(
            status_code=404,
            content={
                "error": f"Entry '{entry_id}' not found in resource '{resource_id}' (version=latest)",
                "errorCode": karp_errors.ClientErrorCodes.ENTRY_NOT_FOUND,
                "resource": resource_id,
                "entry_id": entry_id,
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
            extra={"resource_id": resource_id, "entry_id": entry_id, "data": data},
        )
        raise


@router.delete(
    "/{resource_id}/{entry_id}/delete",
    tags=["Editing"],
    status_code=status.HTTP_204_NO_CONTENT,
)
@router.delete(
    "/{resource_id}/{entry_id}",
    tags=["Editing"],
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_entry(
    resource_id: str,
    entry_id: UniqueIdStr,
    user: User = Security(deps.get_user, scopes=["write"]),
    auth_service: AuthService = Depends(deps.get_auth_service),
    deleting_entry_uc: lex.DeletingEntry = Depends(deps.get_lex_uc(lex.DeletingEntry)),
):
    """Delete a entry from a resource."""
    if not auth_service.authorize(PermissionLevel.write, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="lexica:write"'},
        )
    try:
        deleting_entry_uc.execute(
            commands.DeleteEntry(
                resource_id=resource_id,
                entity_id=unique_id.parse(entry_id),
                user=user.identifier,
            )
        )
    except errors.EntryNotFound:
        return responses.JSONResponse(
            status_code=404,
            content={
                "error": f"Entry '{entry_id}' not found in resource '{resource_id}' (version=latest)",
                "errorCode": karp_errors.ClientErrorCodes.ENTRY_NOT_FOUND,
                "resource": resource_id,
                "entity_id": entry_id,
            },
        )
    return


def init_app(app):
    app.include_router(router)
