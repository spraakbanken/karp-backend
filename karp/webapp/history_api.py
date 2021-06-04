from karp.webapp import schemas
from typing import Dict, Optional

from fastapi import APIRouter, Query, Security, HTTPException, status

from karp.domain import auth_service, model
from karp.domain.models.user import User


from karp.services import entry_views
from karp.utility import unique_id
from .app_config import bus, get_current_user

# from flask import Blueprint, jsonify, request  # pyre-ignore

# import karp.auth.auth as auth
# import karp.resourcemgr.entryread as entryread
# import karp.resourcemgr as resourcemgr
# import karp.errors as errors

# pylint: disable=unsubscriptable-object

router = APIRouter()


@router.get(
    "/{resource_id}/{entry_id}/diff", response_model=entry_views.EntryDiffResponse
)
# @router.post("/{resource_id}/{entry_id}/diff")
# @auth.auth.authorization("ADMIN")
def get_diff(
    resource_id: str,
    entry_id: str,
    user: User = Security(get_current_user, scopes=["admin"]),
    from_version: Optional[int] = None,
    to_version: Optional[int] = None,
    from_date: Optional[float] = None,
    to_date: Optional[float] = None,
    entry: Optional[Dict] = None,
):
    if not bus.ctx.auth_service.authorize(
        auth_service.PermissionLevel.admin, user, [resource_id]
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
    diff_request = entry_views.EntryDiffRequest(
        resource_id=resource_id,
        entry_id=entry_id,
        from_version=from_version,
        to_version=to_version,
        from_date=from_date,
        to_date=to_date,
        entry=entry,
    )
    return entry_views.diff(
        diff_request,
        ctx=bus.ctx,
    )


@router.get(
    "/{resource_id}/history",
)
def get_history(
    resource_id: str,
    user: User = Security(get_current_user, scopes=["admin"]),
    user_id: Optional[str] = Query(None),
    entry_id: Optional[str] = Query(None),
    from_date: Optional[float] = Query(None),
    to_date: Optional[float] = Query(None),
    to_version: Optional[int] = Query(None),
    from_version: Optional[int] = Query(None),
    current_page: int = Query(0),
    page_size: int = Query(100),
):
    if not bus.ctx.auth_service.authorize(
        auth_service.PermissionLevel.admin, user, [resource_id]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="admin"'},
        )
    history_request = entry_views.EntryHistoryRequest(
        page_size=page_size,
        current_page=current_page,
        from_date=from_date,
        to_date=to_date,
        user_id=user_id,
        entry_id=entry_id,
        from_version=from_version,
        to_version=to_version,
    )
    history, total = entry_views.get_history(
        resource_id,
        history_request,
        ctx=bus.ctx,
    )
    return {"history": history, "total": total}


@router.get("/{resource_id}/{entry_id}/{version}/history", response_model=schemas.Entry)
# @auth.auth.authorization("ADMIN")
def get_history_for_entry(
    resource_id: str,
    entry_id: str,
    version: int,
    user: User = Security(get_current_user, scopes=["read"]),
):
    if not bus.ctx.auth_service.authorize(
        auth_service.PermissionLevel.admin, user, [resource_id]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="read"'},
        )
    historical_entry = entry_views.get_entry_history(
        resource_id, entry_id, version=version, ctx=bus.ctx
    )

    return historical_entry


def init_app(app):
    app.include_router(router)
