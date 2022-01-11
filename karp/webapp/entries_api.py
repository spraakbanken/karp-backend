import logging

from fastapi import (APIRouter, Depends, HTTPException, Response, Security,
                     status)
from starlette import responses

from karp import errors as karp_errors
from karp.lex.application.queries import EntryViews
from karp.lex.domain import commands, errors
from karp.auth import User
from karp.foundation.commands import CommandBus
from karp.foundation.value_objects import PermissionLevel, unique_id
# from karp.errors import KarpError
# import karp.auth.auth as auth
# from karp.util import convert
from karp.auth import AuthService
from karp.webapp import schemas

from .app_config import get_current_user
from .fastapi_injector import inject_from_req

# from karp.application.services import entries

# from karp.application import ctx


# from karp.webapp.auth import get_current_user


# from flask import Blueprint  # pyre-ignore
# from flask import jsonify as flask_jsonify  # pyre-ignore
# from flask import request  # pyre-ignore

# from karp.resourcemgr import entrywrite


# edit_api = Blueprint("edit_api", __name__)

router = APIRouter(tags=["Editing"])

logger = logging.getLogger(__name__)


@router.post("/{resource_id}/add", status_code=status.HTTP_201_CREATED)
def add_entry(
    resource_id: str,
    data: schemas.EntryAdd,
    user: User = Security(get_current_user, scopes=["write"]),
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
        return responses.JSONResponse(status_code=400, content={'error': str(exc), 'errorCode': karp_errors.ClientErrorCodes.ENTRY_NOT_VALID})

    entry = entry_views.get_by_id(resource_id, id_)
    return {"newID": entry.entry_id, "uuid": id_}


@router.post("/{resource_id}/{entry_id}/update")
# @auth.auth.authorization("WRITE", add_user=True)
def update_entry(
    response: Response,
    resource_id: str,
    entry_id: str,
    data: schemas.EntryUpdate,
    user: User = Security(get_current_user, scopes=["write"]),
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


@router.delete('/{resource_id}/{entry_id}/delete')
@router.delete('/{resource_id}/{entry_id}')
# @auth.auth.authorization("WRITE", add_user=True)
def delete_entry(
    resource_id: str,
    entry_id: str,
    user: User = Security(get_current_user, scopes=["write"]),
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
