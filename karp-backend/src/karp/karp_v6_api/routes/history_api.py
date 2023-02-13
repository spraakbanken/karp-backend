from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Security, status

from karp.auth import AuthService  # noqa: F401
from karp import auth, lex
from karp.foundation.value_objects import unique_id
from karp.foundation.value_objects.unique_id import UniqueIdStr

from karp.lex.application.queries import (
    EntryDiffDto,
    EntryDto,  # noqa: F401
    EntryDiffRequest,
    EntryHistoryRequest,
    GetEntryDiff,
    GetHistory,
    GetEntryHistory,  # noqa: F401
)
from karp.karp_v6_api import schemas  # noqa: F401

from karp.karp_v6_api import dependencies as deps
from karp.karp_v6_api.dependencies.fastapi_injector import inject_from_req  # noqa: F401


# pylint: disable=unsubscriptable-object

router = APIRouter()


@router.post("/diff/{resource_id}/{entry_id}", response_model=EntryDiffDto)
def get_diff(
    resource_id: str,
    entry_id: UniqueIdStr,
    user: auth.User = Security(deps.get_user, scopes=["admin"]),  # noqa: B008
    from_version: Optional[int] = None,
    to_version: Optional[int] = None,
    from_date: Optional[float] = None,
    to_date: Optional[float] = None,
    entry: Optional[Dict] = None,
    auth_service: auth.AuthService = Depends(deps.get_auth_service),  # noqa: B008
    get_entry_diff: GetEntryDiff = Depends(deps.get_entry_diff),  # noqa: B008
):
    if not auth_service.authorize(auth.PermissionLevel.admin, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="admin"'},
        )

    diff_request = EntryDiffRequest(
        resource_id=resource_id,
        entity_id=unique_id.parse(entry_id),
        from_version=from_version,
        to_version=to_version,
        from_date=from_date,
        to_date=to_date,
        entry=entry,
    )
    return get_entry_diff.query(diff_request)


@router.get(
    "/{resource_id}",
    response_model=lex.GetHistoryDto,
)
def get_history(
    resource_id: str,
    user: auth.User = Security(deps.get_user, scopes=["admin"]),  # noqa: B008
    user_id: Optional[str] = Query(None),  # noqa: B008
    entry_id: Optional[UniqueIdStr] = Query(None),  # noqa: B008
    from_date: Optional[float] = Query(None),  # noqa: B008
    to_date: Optional[float] = Query(None),  # noqa: B008
    to_version: Optional[int] = Query(None),  # noqa: B008
    from_version: Optional[int] = Query(None),  # noqa: B008
    current_page: int = Query(0),  # noqa: B008
    page_size: int = Query(100),  # noqa: B008
    auth_service: auth.AuthService = Depends(deps.get_auth_service),  # noqa: B008
    get_history: GetHistory = Depends(deps.get_history),  # noqa: B008
):
    if not auth_service.authorize(auth.PermissionLevel.admin, user, [resource_id]):
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
    return get_history.query(history_request)


def init_app(app):
    app.include_router(router)
