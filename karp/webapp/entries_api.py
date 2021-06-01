from os import stat
from fastapi import APIRouter, Security, HTTPException, status, Response
from starlette import responses

from karp.domain import commands
from karp.domain.models.user import User
from karp.domain.auth_service import PermissionLevel

# from karp.application.services import entries

# from karp.application import ctx

from karp.webapp import schemas

# from karp.webapp.auth import get_current_user

from karp import errors

# from flask import Blueprint  # pyre-ignore
# from flask import jsonify as flask_jsonify  # pyre-ignore
# from flask import request  # pyre-ignore

# from karp.resourcemgr import entrywrite

# from karp.errors import KarpError
# import karp.auth.auth as auth
# from karp.util import convert
from karp.utility import unique_id
from .app_config import bus, get_current_user

# edit_api = Blueprint("edit_api", __name__)

router = APIRouter()


@router.post("/{resource_id}/add", status_code=status.HTTP_201_CREATED)
def add_entry(
    resource_id: str,
    data: schemas.EntryAdd,
    user: User = Security(get_current_user, scopes=["write"]),
):
    if not bus.ctx.auth_service.authorize(PermissionLevel.write, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="write"'},
        )
    print("calling entrywrite")
    id_ = unique_id.make_unique_id()
    entry_id = None
    bus.handle(
        commands.AddEntry(
            resource_id=resource_id,
            entry_id=entry_id,
            id=id_,
            user=user.identifier,
            message=data.message,
            entry=data.entry,
        )
    )
    # new_entry = entries.add_entry(
    #     resource_id, data.entry, user.identifier, message=data.message
    # )
    return {"newID": entry_id, "uuid": id_}


@router.post("/{resource_id}/{entry_id}/update")
# @auth.auth.authorization("WRITE", add_user=True)
def update_entry(
    response: Response,
    resource_id: str,
    entry_id: str,
    data: schemas.EntryUpdate,
    user: User = Security(get_current_user, scopes=["write"]),
):
    if not ctx.auth_service.authorize(PermissionLevel.write, user, [resource_id]):
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
    print(f"update: data = {data}")
    try:
        new_id = entries.update_entry(
            resource_id,
            entry_id,
            data.version,
            data.entry,
            user.identifier,
            message=data.message,
            # force=force_update,
        )
        return {"newID": new_id}
    except errors.UpdateConflict as err:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return err.error_obj


@router.delete("/{resource_id}/{entry_id}/delete")
# @auth.auth.authorization("WRITE", add_user=True)
def delete_entry(
    resource_id: str,
    entry_id: str,
    user: User = Security(get_current_user, scopes=["write"]),
):
    """Delete a entry from a resource.

    Arguments:
        user {karp.auth.user.User} -- [description]
        resource_id {str} -- [description]
        entry_id {str} -- [description]

    Returns:
        [type] -- [description]
    """
    if not ctx.auth_service.authorize(PermissionLevel.write, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="write"'},
        )
    entries.delete_entry(resource_id, entry_id, user.identifier)
    return "", 204


# @edit_api.route("/{resource_id}/preview", methods=["POST"])
# @auth.auth.authorization("READ")
# def preview_entry(resource_id):
#     data = request.get_json()
#     preview = entrywrite.preview_entry(resource_id, data)
#     return flask_jsonify(preview)


def init_app(app):
    app.include_router(router)
