import logging  # noqa: I001
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from karp import auth
from karp.api import dependencies as deps
from karp.api.dependencies.fastapi_injector import inject_from_req
from karp.auth.application import ResourcePermissionQueries
from karp.lex.application import SearchQueries
from karp.lex.domain.errors import ResourceNotFound
from karp.search.domain import QueryRequest
from karp.search.domain.highlight_param import HighlightParam

from .. import schemas

logger = logging.getLogger(__name__)


router = APIRouter()


@router.get(
    "/entries/{resource_id}/{entry_ids}",
    description="Returns a list of entries matching the given ids",
    name="Get entries by id",
    response_model=schemas.EntriesByIdResponse,
    openapi_extra={"x-openapi-router-order": 3},
)
def get_entries_by_id(
    resource_id: str = Path(..., description="The resource to perform operation on"),
    entry_ids: str = Path(
        ...,
        description="Comma-separated. The ids to perform operation on.",
        pattern=r"^\w(,\w)*",
    ),
    user: auth.User = Depends(deps.get_user_optional),
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permission_queries),
    search_queries: SearchQueries = Depends(inject_from_req(SearchQueries)),
    published_resources: List[str] = Depends(deps.get_published_resources),
):
    logger.debug("karp_v6_api.views.get_entries_by_id")
    if not resource_permissions.has_permission(auth.PermissionLevel.read, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    if resource_id not in published_resources:
        raise ResourceNotFound(resource_id)
    return search_queries.search_ids(resource_id, entry_ids.split(","))


@router.get(
    "/stats/{resources}",
    summary="Get statistics for search",
    description="Same as `/query`, but without returning the hits.",
    response_model=schemas.QueryStatsResponse,
    openapi_extra={"x-openapi-router-order": 2},
)
def query_stats(
    resources: str = Path(
        ...,
        pattern=r"^[a-z_0-9\-]+(,[a-z_0-9\-]+)*$",
        description="A comma-separated list of resource identifiers",
    ),
    q: Optional[str] = Query(
        None,
        title="query",
        description="""The query. If missing, the number of entries in the chosen resource(s) 
            will be returned. See [Query DSL](#section/Query-DSL)""",
    ),
    user: auth.User = Depends(deps.get_user_optional),
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permission_queries),
    search_queries: SearchQueries = Depends(inject_from_req(SearchQueries)),
    published_resources: List[str] = Depends(deps.get_published_resources),
):
    resource_list = resources.split(",")
    if not resource_permissions.has_permission(auth.PermissionLevel.read, user, resource_list):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    if any(resource not in published_resources for resource in resource_list):
        raise ResourceNotFound(resource_list)
    response = search_queries.query_stats(resource_list, q)
    return response


@router.get(
    "/{resources}",
    summary="Search",
    response_model=schemas.QueryResponse,
    openapi_extra={"x-openapi-router-order": 1},
)
def query(
    resources: str = Path(
        ...,
        pattern=r"^[a-z_0-9\-]+(,[a-z_0-9\-]+)*$",
        description="A comma-separated list of resource identifiers",
    ),
    q: Optional[str] = Query(
        None,
        title="query",
        description="The query. If missing, all entries in chosen resource(s) will be returned. See [Searching](#section/Searching)",
    ),
    from_: int = Query(0, alias="from", description="Specify which entry should be the first returned."),
    size: int = Query(25, description="Number of entries in page."),
    sort: str = Query(
        [],
        description="The `field` to sort by. If missing, default order for each resource will be used.",
        # pattern is only supported for str, not list[str]
        # pattern=r"^[a-zA-Z0-9_\-]+(\|asc|desc)?",
    ),
    lexicon_stats: bool = Query(True, description="Show the hit count per lexicon"),
    path: Optional[str] = Query(
        None,
        description="""A dot-separataed path to for returning a specific field in JSON. 
        Only supports one path down into the tree with no indexing.
        For example, to fetch only the field `baseform` in the entry, use: `?path=entry.baseform`
        If the selected field is an array, the result will also be wrapped in an array.""",
    ),
    highlight: HighlightParam = Query(
        HighlightParam.false,
        description="""Adds which fields the query matched and a small hit context with `<em>` wrapped around the match.
                        For compatibility reasons the values are true/new/false. true gives an older version of the highlight and
                        new gives the future format, which includes indices for lists.""",
    ),
    user: auth.User = Depends(deps.get_user_optional),
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permission_queries),
    search_queries: SearchQueries = Depends(inject_from_req(SearchQueries)),
    published_resources: List[str] = Depends(deps.get_published_resources),
):
    """
    Returns a list of entries matching the given query in the given resources. The results are mixed from the given resources.

    """
    sort = sort.split(",") if sort else ()
    logger.debug(
        "Called 'query' called with",
        extra={"resources": resources, "from": from_, "size": size},
    )
    resource_list = resources.split(",")
    if not resource_permissions.has_permission(auth.PermissionLevel.read, user, resource_list):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    if any(resource not in published_resources for resource in resource_list):
        raise ResourceNotFound(resource_list)
    query_request = QueryRequest(
        resources=resource_list,
        q=q,
        from_=from_,
        size=size,
        sort=sort,
        path=path,
        lexicon_stats=lexicon_stats,
        highlight=highlight,
    )
    logger.debug(f"{search_queries=}")
    response = search_queries.query(query_request)
    return response
