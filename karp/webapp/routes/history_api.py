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
from karp.webapp import schemas

from karp.webapp.dependencies.auth import get_user
from karp.webapp.dependencies.fastapi_injector import inject_from_req


# pylint: disable=unsubscriptable-object

router = APIRouter()


@router.get(
    "/diff/{resource_id}/{entry_id}", response_model=EntryDiffDto
)
# @router.post("/{resource_id}/{entry_id}/diff")
# @auth.auth.authorization("ADMIN")
def get_diff(
    resource_id: str,
    entry_id: str,
    user: auth.User = Security(get_user, scopes=["admin"]),
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
    '/{resource_id}',
)
@router.get(
    '/of-resource/{resource_id}',
)
def get_history(
    resource_id: str,
    user: auth.User = Security(get_user, scopes=["admin"]),
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




def init_app(app):
    app.include_router(router)
