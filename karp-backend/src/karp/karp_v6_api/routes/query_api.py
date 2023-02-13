"""
Query API.

## Query DSL
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Security, status

from karp import auth, search
from karp.main import errors as karp_errors
from karp.search.application.queries import SearchService, QueryRequest
from karp.karp_v6_api import schemas

from karp.karp_v6_api import dependencies as deps
from karp.karp_v6_api.dependencies.fastapi_injector import inject_from_req


logger = logging.getLogger(__name__)


router = APIRouter()


@router.get(
    "/entries/{resource_id}/{entry_ids}",
    description="Returns a list of entries matching the given ids",
    name="Get lexical entries by id",
)
def get_entries_by_id(
    resource_id: str = Path(
        ..., description="The resource to perform operation on"
    ),  # noqa: B008
    entry_ids: str = Path(  # noqa: B008
        ...,
        description="Comma-separated. The ids to perform operation on.",
        regex=r"^\w(,\w)*",
    ),
    user: auth.User = Security(deps.get_user_optional, scopes=["read"]),  # noqa: B008
    auth_service: auth.AuthService = Depends(deps.get_auth_service),  # noqa: B008
    search_service: SearchService = Depends(
        inject_from_req(SearchService)
    ),  # noqa: B008
):
    logger.debug("karp_v6_api.views.get_entries_by_id")
    if not auth_service.authorize(auth.PermissionLevel.read, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="read"'},
        )
    return search_service.search_ids(resource_id, entry_ids)


@router.get("/split/{resources}", name="Query per resource")
def query_split(
    resources: str = Path(  # noqa: B008
        ...,
        regex=r"^[a-z_0-9\-]+(,[a-z_0-9\-]+)*$",
        description="A comma-separated list of resource identifiers",
    ),
    q: Optional[str] = Query(  # noqa: B008
        None,
        title="query",
        description="The query. If missing, all entries in chosen resource(s) will be returned.",
    ),
    from_: int = Query(  # noqa: B008
        0, alias="from", description="Specify which entry should be the first returned."
    ),
    size: int = Query(25, description="Number of entries in page."),  # noqa: B008
    sort: str = Query(  # noqa: B008
        None,
        description="The `field` to sort by. If missing, default order for each resource will be used.",
        regex=r"^[a-zA-Z0-9_\-]+(\|asc|desc)?",
    ),
    lexicon_stats: bool = Query(
        True, description="Show the hit count per lexicon"
    ),  # noqa: B008
    include_fields: Optional[List[str]] = Query(  # noqa: B008
        None, description="Comma-separated list of which fields to return"
    ),
    exclude_fields: Optional[List[str]] = Query(  # noqa: B008
        None, description="Comma-separated list of which fields to remove from result"
    ),
    format: schemas.EntryFormat = Query(  # noqa: B008
        schemas.EntryFormat.json,
        description="Will return the result in the specified format.",
    ),
    user: auth.User = Security(deps.get_user_optional, scopes=["read"]),  # noqa: B008
    auth_service: auth.AuthService = Depends(deps.get_auth_service),  # noqa: B008
    search_service: SearchService = Depends(
        inject_from_req(SearchService)
    ),  # noqa: B008
):
    logger.debug("/query/split called", extra={"resources": resources})
    resource_list = resources.split(",")
    if not auth_service.authorize(auth.PermissionLevel.read, user, resource_list):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="read"'},
        )
    query_request = QueryRequest(
        resource_ids=resource_list,
        q=q,
        from_=from_,
        size=size,
        lexicon_stats=lexicon_stats,
    )
    try:
        response = search_service.query_split(query_request)
    except karp_errors.KarpError as err:
        logger.exception(
            "Error occured when calling '/query/split'",
            extra={"resources": resources, "q": q, "error_message": err.message},
        )
        raise
    except search.IncompleteQuery as err:
        raise HTTPException(  # noqa: B904
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "errorCode": karp_errors.ClientErrorCodes.SEARCH_INCOMPLETE_QUERY,
                "message": "Error in query",
                "failing_query": err.failing_query,
                "error_description": err.error_description,
            },
        )
    return response


@router.get(
    "/{resources}",
    # summary="Returns a list of entries matching the given query in the given resources. The results are mixed from the given resources.",
    name="Query",
    responses={200: {"content": {"application/json": {}}}},
)
def query(
    resources: str = Path(  # noqa: B008
        ...,
        regex=r"^[a-z_0-9\-]+(,[a-z_0-9\-]+)*$",
        description="A comma-separated list of resource identifiers",
    ),
    q: Optional[str] = Query(  # noqa: B008
        None,
        title="query",
        description="The query. If missing, all entries in chosen resource(s) will be returned.",
    ),
    from_: int = Query(  # noqa: B008
        0, alias="from", description="Specify which entry should be the first returned."
    ),
    size: int = Query(25, description="Number of entries in page."),  # noqa: B008
    sort: List[str] = Query(  # noqa: B008
        [],
        description="The `field` to sort by. If missing, default order for each resource will be used.",
        regex=r"^[a-zA-Z0-9_\-]+(\|asc|desc)?",
    ),
    lexicon_stats: bool = Query(
        True, description="Show the hit count per lexicon"
    ),  # noqa: B008
    include_fields: Optional[List[str]] = Query(  # noqa: B008
        None, description="Comma-separated list of which fields to return"
    ),
    exclude_fields: Optional[List[str]] = Query(  # noqa: B008
        None, description="Comma-separated list of which fields to remove from result"
    ),
    format_: schemas.EntryFormat = Query(  # noqa: B008
        schemas.EntryFormat.json,
        alias="format",
        description="Will return the result in the specified format.",
    ),
    user: auth.User = Security(deps.get_user_optional, scopes=["read"]),  # noqa: B008
    auth_service: auth.AuthService = Depends(deps.get_auth_service),  # noqa: B008
    search_service: SearchService = Depends(
        inject_from_req(SearchService)
    ),  # noqa: B008
):
    """
    Returns a list of entries matching the given query in the given resources. The results are mixed from the given resources.

    """
    logger.debug(
        "Called 'query' called with",
        extra={"resources": resources, "from": from_, "size": size},
    )
    resource_list = resources.split(",")
    if not auth_service.authorize(auth.PermissionLevel.read, user, resource_list):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="read"'},
        )
    query_request = QueryRequest(
        resource_ids=resource_list,
        q=q,
        from_=from_,
        size=size,
        sort=sort,
        include_fields=include_fields,
        exclude_fields=exclude_fields,
        format_=format_,
        lexicon_stats=lexicon_stats,
    )
    try:
        print(f"{search_service=}")
        response = search_service.query(query_request)

    except karp_errors.KarpError as err:
        logger.exception(
            "Error occured when calling 'query' with",
            extra={"resources": resources, "q": q, "error_message": err.message},
        )
        raise
    return response


def init_app(app):
    app.include_router(router)
