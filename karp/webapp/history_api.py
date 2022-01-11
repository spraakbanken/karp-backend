from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Security, status

from karp.auth import AuthService
from karp import auth

from karp.lex.application.queries import (
    EntryDiffDto,
    EntryDto,
    EntryDiffRequest,
    EntryHistoryRequest,
    GetEntryDiff,
    GetHistory,
    GetEntryHistory,
)
# from karp.domain import model, value_objects
# from karp.domain.models.user import User
# from karp.domain.value_objects import unique_id
# from karp.services import entry_views
# from karp.services.auth_service import AuthService
# from karp.services.messagebus import MessageBus
from karp.webapp import schemas

from .app_config import get_current_user
from .fastapi_injector import inject_from_req

# from flask import Blueprint, jsonify, request  # pyre-ignore

# import karp.auth.auth as auth
# import karp.resourcemgr.entryread as entryread
# import karp.resourcemgr as resourcemgr
# import karp.errors as errors

# pylint: disable=unsubscriptable-object

router = APIRouter(tags=["History"])


@router.get(
    "/{resource_id}/{entry_id}/diff", response_model=EntryDiffDto
)
# @router.post("/{resource_id}/{entry_id}/diff")
# @auth.auth.authorization("ADMIN")
def get_diff(
    resource_id: str,
    entry_id: str,
    user: auth.User = Security(get_current_user, scopes=["admin"]),
    from_version: Optional[int] = None,
    to_version: Optional[int] = None,
    from_date: Optional[float] = None,
    to_date: Optional[float] = None,
    entry: Optional[Dict] = None,
    auth_service: AuthService = Depends(inject_from_req(AuthService)),
    get_entry_diff: GetEntryDiff = Depends(inject_from_req(GetEntryDiff)),
):
    if not auth_service.authorize(
        auth.PermissionLevel.admin, user, [resource_id]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="admin"'},
        )
    #     from_version = request.args.get("from_version")
    #     to_version = request.args.get("to_version")
    #     from_date_str = request.args.get("from_date")
    #     to_date_str = request.args.get("to_date")
    #     from_date = None
    #     to_date = None
    #     try:
    #         if from_date_str:
    #             from_date = float(from_date_str)
    #         if to_date_str:
    #             to_date = float(to_date_str)
    #     except ValueError:
    #         raise errors.KarpError("Wrong date format", code=50)
    #
    #     diff_parameters = {
    #         "from_date": from_date,
    #         "to_date": to_date,
    #         "from_version": from_version,
    #         "to_version": to_version,
    #         "entry": request.get_json(),
    #     }
    #
    diff_request = EntryDiffRequest(
        resource_id=resource_id,
        entry_id=entry_id,
        from_version=from_version,
        to_version=to_version,
        from_date=from_date,
        to_date=to_date,
        entry=entry,
    )
    return get_entry_diff.query(diff_request)


@router.get(
    "/{resource_id}/history",
)
def get_history(
    resource_id: str,
    user: auth.User = Security(get_current_user, scopes=["admin"]),
    user_id: Optional[str] = Query(None),
    entry_id: Optional[str] = Query(None),
    from_date: Optional[float] = Query(None),
    to_date: Optional[float] = Query(None),
    to_version: Optional[int] = Query(None),
    from_version: Optional[int] = Query(None),
    current_page: int = Query(0),
    page_size: int = Query(100),
    auth_service: AuthService = Depends(inject_from_req(AuthService)),
    get_history: GetHistory = Depends(inject_from_req(GetHistory)),
):
    if not auth_service.authorize(
        auth.PermissionLevel.admin, user, [resource_id]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="admin"'},
        )
    history_request = EntryHistoryRequest(
        resource_id=resource_id,
        page_size=page_size,
        current_page=current_page,
        from_date=from_date,
        to_date=to_date,
        user_id=user_id,
        entry_id=entry_id,
        from_version=from_version,
        to_version=to_version,
    )
    history, total = get_history.query(history_request)
    return {"history": history, "total": total}


@router.get("/{resource_id}/{entry_id}/{version}/history", response_model=EntryDto)
# @auth.auth.authorization("ADMIN")
def get_history_for_entry(
    resource_id: str,
    entry_id: str,
    version: int,
    user: auth.User = Security(get_current_user, scopes=["read"]),
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
            headers={"WWW-Authenticate": 'Bearer scope="read"'},
        )
    historical_entry = get_entry_history.query(
        resource_id, entry_id, version=version
    )

    return historical_entry


def init_app(app):
    app.include_router(router)
