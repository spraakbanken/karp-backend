from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from karp import auth
from karp.api import dependencies as deps
from karp.auth.application import ResourcePermissionQueries
from karp.auth.domain.user import User
from karp.foundation.value_objects import unique_id
from karp.foundation.value_objects.unique_id import UniqueIdStr
from karp.lex.application import EntryQueries
from karp.lex.application.dtos import (
    EntryDiffDto,
    EntryDiffRequest,
    EntryHistoryRequest,
    GetHistoryDto,
)

router = APIRouter()


@router.post("/diff/{resource_id}/{entry_id}", response_model=EntryDiffDto)
def get_diff(
    resource_id: str,
    entry_id: UniqueIdStr,
    user: User = Depends(deps.get_user_optional),
    from_version: Optional[int] = None,
    to_version: Optional[int] = None,
    from_date: Optional[float] = None,
    to_date: Optional[float] = None,
    entry: Optional[Dict] = None,
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permission_queries),
    entry_queries: EntryQueries = Depends(deps.get_entry_queries),
):
    if not resource_permissions.has_permission(auth.PermissionLevel.write, user, [resource_id]):
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
    response_model=GetHistoryDto,
)
def get_history(
    resource_id: str,
    user: User = Depends(deps.get_user_optional),
    user_id: Optional[str] = Query(None),
    entry_id: Optional[UniqueIdStr] = Query(None),
    from_date: Optional[float] = Query(None),
    to_date: Optional[float] = Query(None),
    to_version: Optional[int] = Query(None),
    from_version: Optional[int] = Query(None),
    current_page: int = Query(0),
    page_size: int = Query(100),
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permission_queries),
    entry_queries: EntryQueries = Depends(deps.get_entry_queries),
):
    if not resource_permissions.has_permission(auth.PermissionLevel.write, user, [resource_id]):
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
