from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Security, status

from karp import auth, lex
from karp.api import dependencies as deps
from karp.auth.infrastructure import ResourcePermissionQueries
from karp.foundation.value_objects import unique_id
from karp.foundation.value_objects.unique_id import UniqueIdStr
from karp.lex.application.queries import (
    EntryDiffDto,
    EntryDiffRequest,
    EntryHistoryRequest,
)
from karp.lex_infrastructure import EntryQueries

router = APIRouter()


@router.post("/diff/{resource_id}/{entry_id}", response_model=EntryDiffDto)
def get_diff(
    resource_id: str,
    entry_id: UniqueIdStr,
    user: auth.User = Security(deps.get_user, scopes=["admin"]),
    from_version: Optional[int] = None,
    to_version: Optional[int] = None,
    from_date: Optional[float] = None,
    to_date: Optional[float] = None,
    entry: Optional[Dict] = None,
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permissions),
    entry_queries: EntryQueries = Depends(deps.get_entry_queries),
):
    if not resource_permissions.has_permission(auth.PermissionLevel.admin, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
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
    return entry_queries.get_entry_diff(diff_request)


@router.get(
    "/{resource_id}",
    response_model=lex.GetHistoryDto,
)
def get_history(
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
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permissions),
    entry_queries: EntryQueries = Depends(deps.get_entry_queries),
):
    if not resource_permissions.has_permission(auth.PermissionLevel.admin, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
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
    return entry_queries.get_history(history_request)


def init_app(app):
    app.include_router(router)
