"""
Query API.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Security, HTTPException, status, Query, Path

from karp import errors as karp_errors

from karp.domain import value_objects, index

from karp.domain.models.user import User

# from karp.domain.models.auth_service import PermissionLevel

# from karp.application import ctx
# from karp.application.services import resources as resources_service

from karp.webapp import schemas

# from karp.webapp.auth import get_current_user
from karp.services import entry_query
from .app_config import bus, get_current_user


_logger = logging.getLogger("karp")


router = APIRouter(tags=["Querying"])


@router.get(
    "/entries/{resource_id}/{entry_ids}",
    description="Returns a list of entries matching the given ids",
)
def get_entries_by_id(
    resource_id: str = Path(..., description="The resource to perform operation on"),
    entry_ids: str = Path(
        ...,
        description="Comma-separated. The ids to perform operation on.",
        regex=r"^\w(,\w)*",
    ),
    user: User = Security(get_current_user, scopes=["read"]),
):
    print("webapp.views.get_entries_by_id")
    if not bus.ctx.auth_service.authorize(
        value_objects.PermissionLevel.read, user, [resource_id], bus.ctx
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="read"'},
        )
    return entry_query.search_ids(resource_id, entry_ids, ctx=bus.ctx)


# @router.get("/{resources}/query")
@router.get("/query/{resources}")
def query(
    resources: str = Path(
        ...,
        regex=r"^\w+(,\w+)*$",
        description="A comma-separated list of resource identifiers",
    ),
    q: Optional[str] = Query(
        None,
        title="query",
        description="The query. If missing, all entries in chosen resource(s) will be returned.",
    ),
    from_: int = Query(
        0, alias="from", description="Specify which entry should be the first returned."
    ),
    size: int = Query(25, description="Number of entries in page."),
    sort: str = Query(
        None,
        description="The `field` to sort by. If missing, default order for each resource will be used.",
        regex=r"^\w+\|(asc|desc)",
    ),
    lexicon_stats: bool = Query(True, description="Show the hit count per lexicon"),
    include_fields: Optional[List[str]] = Query(
        None, description="Comma-separated list of which fields to return"
    ),
    exclude_fields: Optional[List[str]] = Query(
        None, description="Comma-separated list of which fields to remove from result"
    ),
    format: schemas.EntryFormat = Query(
        schemas.EntryFormat.json,
        description="Will return the result in the specified format.",
    ),
    user: User = Security(get_current_user, scopes=["read"]),
):
    print(
        f"Called 'query' called with resources={resources}, from={from_}m size={size}"
    )
    resource_list = resources.split(",")
    if not bus.ctx.auth_service.authorize(
        value_objects.PermissionLevel.read, user, resource_list, bus.ctx
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="read"'},
        )
    query_request = index.QueryRequest(
        resource_ids=resource_list,
        q=q,
        from_=from_,
        size=size,
        lexicon_stats=lexicon_stats,
    )
    try:
        response = entry_query.query(query_request, ctx=bus.ctx)

    except karp_errors.KarpError as err:
        _logger.exception(
            "Error occured when calling 'query' with resources='%s' and q='%s'. e.msg='%s'",
            resources,
            q,
            err.message,
        )
        raise
    return response


# @router.get("/{resources}/query_split")
@router.get("/query_split/{resources}")
def query_split(
    resources: str = Path(
        ...,
        regex=r"^\w+(,\w+)*$",
        description="A comma-separated list of resource identifiers",
    ),
    q: Optional[str] = Query(
        None,
        title="query",
        description="The query. If missing, all entries in chosen resource(s) will be returned.",
    ),
    from_: int = Query(
        0, alias="from", description="Specify which entry should be the first returned."
    ),
    size: int = Query(25, description="Number of entries in page."),
    sort: str = Query(
        None,
        description="The `field` to sort by. If missing, default order for each resource will be used.",
        regex=r"^\w+\|(asc|desc)",
    ),
    lexicon_stats: bool = Query(True, description="Show the hit count per lexicon"),
    include_fields: Optional[List[str]] = Query(
        None, description="Comma-separated list of which fields to return"
    ),
    exclude_fields: Optional[List[str]] = Query(
        None, description="Comma-separated list of which fields to remove from result"
    ),
    format: schemas.EntryFormat = Query(
        schemas.EntryFormat.json,
        description="Will return the result in the specified format.",
    ),
    user: User = Security(get_current_user, scopes=["read"]),
):
    print("webapp.views.query.query_split: called with resources={}".format(resources))
    resource_list = resources.split(",")
    if not bus.ctx.auth_service.authorize(
        value_objects.PermissionLevel.read, user, resource_list, bus.ctx
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="read"'},
        )
    query_request = index.QueryRequest(
        resource_ids=resource_list,
        q=q,
        from_=from_,
        size=size,
        lexicon_stats=lexicon_stats,
    )
    try:
        response = entry_query.query_split(query_request, ctx=bus.ctx)

    except karp_errors.KarpError as err:
        _logger.exception(
            "Error occured when calling 'query_split' with resources='%s' and q='%s'. msg='%s'",
            resources,
            q,
            err.message,
        )
        raise
    return response


def init_app(app):
    app.include_router(router)
