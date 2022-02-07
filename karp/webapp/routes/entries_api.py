import logging
from typing import Optional

from fastapi import (APIRouter, Depends, HTTPException, Response, Security,
                     status, Path, Query)
from starlette import responses

from karp import errors as karp_errors, auth
from karp.lex.application.queries import EntryViews, EntryDto, GetEntryHistory
from karp.lex.domain import commands, errors
from karp.auth import User
from karp.foundation.commands import CommandBus
from karp.foundation.value_objects import PermissionLevel, unique_id
from karp.auth import AuthService
from karp.webapp import schemas

from karp.webapp.dependencies.auth import get_user
from karp.webapp.dependencies.fastapi_injector import inject_from_req

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get('/{resource_id}/{entry_id}/{version}', response_model=EntryDto)
@router.get('/{resource_id}/{entry_id}', response_model=EntryDto)
# @auth.auth.authorization("ADMIN")
def get_history_for_entry(
    resource_id: str,
    entry_id: str,
    version: Optional[int] = Query(None),
    user: auth.User = Security(get_user, scopes=["admin"]),
    auth_service: AuthService = Depends(inject_from_req(AuthService)),
    get_entry_history: GetEntryHistory = Depends(
        inject_from_req(GetEntryHistory)),
):
    if not auth_service.authorize(
        auth.PermissionLevel.admin, user, [resource_id]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="lexica:admin"'},
        )
    historical_entry = get_entry_history.query(
        resource_id, entry_id, version=version
    )

    return historical_entry


@router.post("/{resource_id}/add", status_code=status.HTTP_201_CREATED, tags=["editing"])
@router.put('/{resource_id}', status_code=status.HTTP_201_CREATED, tags=["editing"])
def add_entry(
    resource_id: str,
    data: schemas.EntryAdd,
    user: User = Security(get_user, scopes=["write"]),
    auth_service: AuthService = Depends(inject_from_req(AuthService)),
    bus: CommandBus = Depends(inject_from_req(CommandBus)),
    entry_views: EntryViews = Depends(inject_from_req(EntryViews)),
):
    if not auth_service.authorize(PermissionLevel.write, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="write"'},
        )
    id_ = unique_id.make_unique_id()
    try:
        bus.dispatch(
            commands.AddEntry(
                resource_id=resource_id,
                entity_id=id_,
                user=user.identifier,
                message=data.message,
                entry=data.entry,
            )
        )
    except errors.IntegrityError as exc:
        return responses.JSONResponse(
            status_code=400,
            content={
                'error': str(exc),
                'errorCode': karp_errors.ClientErrorCodes.DB_INTEGRITY_ERROR
            }
        )
    except errors.InvalidEntry as exc:
        return responses.JSONResponse(
            status_code=400,
            content={
                'error': str(exc),
                'errorCode': karp_errors.ClientErrorCodes.ENTRY_NOT_VALID
            }
        )

    entry = entry_views.get_by_id(resource_id, id_)
    return {"newID": entry.entry_id, "uuid": id_}


@router.post("/{resource_id}/{entry_id}/update", tags=["editing"])
@router.post('/{resource_id}/{entry_id}', tags=["editing"])
# @auth.auth.authorization("WRITE", add_user=True)
def update_entry(
    response: Response,
    resource_id: str,
    entry_id: str,
    data: schemas.EntryUpdate,
    user: User = Security(get_user, scopes=["write"]),
    auth_service: AuthService = Depends(inject_from_req(AuthService)),
    bus: CommandBus = Depends(inject_from_req(CommandBus)),
    entry_views: EntryViews = Depends(inject_from_req(EntryViews)),
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
    try:
        entry = entry_views.get_by_entry_id(resource_id, entry_id)
        bus.dispatch(
            commands.UpdateEntry(
                resource_id=resource_id,
                entity_id=entry.entry_uuid,
                entry_id=entry_id,
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
        entry = entry_views.get_by_id(resource_id, entry.entry_uuid)
        return {"newID": entry.entry_id, "uuid": entry.entry_uuid}
    except errors.EntryNotFound:
        return responses.JSONResponse(
            status_code=404,
            content={
                'error': f"Entry '{entry_id}' not found in resource '{resource_id}' (version=latest)",
                'errorCode': karp_errors.ClientErrorCodes.ENTRY_NOT_FOUND,
                'resource': resource_id,
                'entry_id': entry_id,
            }
        )
    except errors.UpdateConflict as err:
        response.status_code = status.HTTP_400_BAD_REQUEST
        err.error_obj["errorCode"] = karp_errors.ClientErrorCodes.VERSION_CONFLICT
        return err.error_obj
    except Exception as err:
        print(f'{err=}')
        raise


@router.delete('/{resource_id}/{entry_id}/delete', tags=["editing"])
@router.delete('/{resource_id}/{entry_id}', tags=["editing"])
# @auth.auth.authorization("WRITE", add_user=True)
def delete_entry(
    resource_id: str,
    entry_id: str,
    user: User = Security(get_user, scopes=["write"]),
    auth_service: AuthService = Depends(inject_from_req(AuthService)),
    bus: CommandBus = Depends(inject_from_req(CommandBus)),
):
    """Delete a entry from a resource.

    Arguments:
        user {karp.auth.user.User} -- [description]
        resource_id {str} -- [description]
        entry_id {str} -- [description]

    Returns:
        [type] -- [description]
    """
    if not auth_service.authorize(PermissionLevel.write, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="write"'},
        )
    try:
        bus.dispatch(
            commands.DeleteEntry(
                resource_id=resource_id,
                entry_id=entry_id,
                user=user.identifier,
            )
        )
    except errors.EntryNotFound:
        return responses.JSONResponse(
            status_code=404,
            content={
                'error': f"Entry '{entry_id}' not found in resource '{resource_id}' (version=latest)",
                'errorCode': karp_errors.ClientErrorCodes.ENTRY_NOT_FOUND,
                'resource': resource_id,
                'entry_id': entry_id,
            }
        )
    # entries.delete_entry(resource_id, entry_id, user.identifier)
    return "", 204


# @edit_api.route("/{resource_id}/preview", methods=["POST"])
# @auth.auth.authorization("READ")
# def preview_entry(resource_id):
#     data = request.get_json()
#     preview = entrywrite.preview_entry(resource_id, data)
#     return flask_jsonify(preview)


def init_app(app):
    app.include_router(router)
