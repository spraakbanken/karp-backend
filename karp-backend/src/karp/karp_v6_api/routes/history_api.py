from typing import Dict, Optional  # noqa: D100, I001

from fastapi import APIRouter, Depends, HTTPException, Query, Security, status

from karp.auth import AuthService  # noqa: F401
from karp import auth, lex
from karp.lex_core.value_objects import unique_id
from karp.lex_core.value_objects.unique_id import UniqueIdStr

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
def get_diff(  # noqa: ANN201, D103
    resource_id: str,
    entry_id: UniqueIdStr,
    user: auth.User = Security(deps.get_user, scopes=["admin"]),
    from_version: Optional[int] = None,
    to_version: Optional[int] = None,
    from_date: Optional[float] = None,
    to_date: Optional[float] = None,
    entry: Optional[Dict] = None,
    auth_service: auth.AuthService = Depends(deps.get_auth_service),
    get_entry_diff: GetEntryDiff = Depends(deps.get_entry_diff),
):
    if not auth_service.authorize(auth.PermissionLevel.admin, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="admin"'},
        )

    diff_request = EntryDiffRequest(
        resourceId=resource_id,
        id=unique_id.parse(entry_id),
        fromVersion=from_version,
        toVersion=to_version,
        fromDate=from_date,
        toDate=to_date,
        entry=entry,
    )
    return get_entry_diff.query(diff_request)


@router.get(
    "/{resource_id}",
    response_model=lex.GetHistoryDto,
)
def get_history(  # noqa: ANN201, D103
    resource_id: str,
    user: auth.User = Security(deps.get_user, scopes=["admin"]),
    user_id: Optional[str] = Query(None),
    entry_id: Optional[UniqueIdStr] = Query(None),
    from_date: Optional[float] = Query(None),
    to_date: Optional[float] = Query(None),
    to_version: Optional[int] = Query(None),
    from_version: Optional[int] = Query(None),
    current_page: int = Query(0),
    page_size: int = Query(100),
    auth_service: auth.AuthService = Depends(deps.get_auth_service),
    get_history: GetHistory = Depends(deps.get_history),
):
    if not auth_service.authorize(auth.PermissionLevel.admin, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="admin"'},
        )
    history_request = EntryHistoryRequest(
        resourceId=resource_id,
        pageSize=page_size,
        currentPage=current_page,
        fromDate=from_date,
        toDate=to_date,
        userId=user_id,
        entryId=entry_id,
        fromVersion=from_version,
        toVersion=to_version,
    )
    return get_history.query(history_request)


def init_app(app):  # noqa: ANN201, D103
    app.include_router(router)
