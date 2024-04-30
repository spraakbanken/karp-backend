import logging  # noqa: I001
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from karp import auth, search
from karp.auth.application import ResourcePermissionQueries
from karp.lex import EntryDto
from karp.lex.domain.errors import ResourceNotFound
from karp.main import errors as karp_errors
from karp.search.domain import QueryRequest
from karp.search.domain.errors import IncompleteQuery

from karp.api import dependencies as deps
from karp.api.dependencies.fastapi_injector import inject_from_req
from karp.search.infrastructure.es import EsSearchService


logger = logging.getLogger(__name__)


router = APIRouter()


@router.get(
    "/entries/{resource_id}/{entry_ids}",
    description="Returns a list of entries matching the given ids",
    name="Get entries by id",
    response_model=List[EntryDto],
)
def get_entries_by_id(
    resource_id: str = Path(..., description="The resource to perform operation on"),
    entry_ids: str = Path(
        ...,
        description="Comma-separated. The ids to perform operation on.",
        regex=r"^\w(,\w)*",
    ),
    user: auth.User = Depends(deps.get_user_optional),
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permissions),
    search_service: EsSearchService = Depends(inject_from_req(EsSearchService)),
    published_resources: [str] = Depends(deps.get_published_resources),
):
    logger.debug("karp_v6_api.views.get_entries_by_id")
    if not resource_permissions.has_permission(auth.PermissionLevel.read, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    if resource_id not in published_resources:
        raise ResourceNotFound(resource_id)
    return search_service.search_ids(resource_id, entry_ids)


@router.get("/stats/{resources}", name="Hits per resource, no entries in result")
def query_stats(
    resources: str = Path(
        ...,
        regex=r"^[a-z_0-9\-]+(,[a-z_0-9\-]+)*$",
        description="A comma-separated list of resource identifiers",
    ),
    q: Optional[str] = Query(
        None,
        title="query",
        description="""The query. If missing, the number of entries in the chosen resource(s) 
            will be returned. See [Query DSL](#section/Query-DSL)""",
    ),
    user: auth.User = Depends(deps.get_user_optional),
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permissions),
    search_service: EsSearchService = Depends(inject_from_req(EsSearchService)),
    published_resources: [str] = Depends(deps.get_published_resources),
):
    resource_list = resources.split(",")
    if not resource_permissions.has_permission(auth.PermissionLevel.read, user, resource_list):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    if any(resource not in published_resources for resource in resource_list):
        raise ResourceNotFound(resource_list)
    try:
        response = search_service.query_stats(resource_list, q)
    except karp_errors.KarpError as err:
        logger.exception(
            "Error occured when calling '/query/stats'",
            extra={"resources": resources, "q": q, "error_message": err.message},
        )
        raise
    except IncompleteQuery as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "errorCode": karp_errors.ClientErrorCodes.SEARCH_INCOMPLETE_QUERY,
                "message": "Error in query",
                "failing_query": err.failing_query,
                "error_description": err.error_description,
            },
        ) from None
    return response


@router.get(
    "/{resources}",
    name="Query",
    responses={200: {"content": {"application/json": {}}}},
)
def query(
    resources: str = Path(
        ...,
        regex=r"^[a-z_0-9\-]+(,[a-z_0-9\-]+)*$",
        description="A comma-separated list of resource identifiers",
    ),
    q: Optional[str] = Query(
        None,
        title="query",
        description="The query. If missing, all entries in chosen resource(s) will be returned. See [Query DSL](#section/Query-DSL)",
    ),
    from_: int = Query(
        0, alias="from", description="Specify which entry should be the first returned."
    ),
    size: int = Query(25, description="Number of entries in page."),
    sort: List[str] = Query(
        [],
        description="The `field` to sort by. If missing, default order for each resource will be used.",
        regex=r"^[a-zA-Z0-9_\-]+(\|asc|desc)?",
    ),
    lexicon_stats: bool = Query(True, description="Show the hit count per lexicon"),
    path: Optional[str] = Query(
        None,
        description="""A dot-separataed path to for returning a specific field in JSON. 
        Only supports one path down into the tree with no indexing.
        For example, to fetch only the field `baseform` in the entry, use: `?path=entry.baseform`
        If the selected field is an array, the result will also be wrapped in an array.""",
    ),
    user: auth.User = Depends(deps.get_user_optional),
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permissions),
    search_service: EsSearchService = Depends(inject_from_req(EsSearchService)),
    published_resources: [str] = Depends(deps.get_published_resources),
):
    """
    Returns a list of entries matching the given query in the given resources. The results are mixed from the given resources.

    """
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
    )
    try:
        logger.debug(f"{search_service=}")
        response = search_service.query(query_request)

    except karp_errors.KarpError as err:
        logger.exception(
            "Error occured when calling 'query' with",
            extra={"resources": resources, "q": q, "error_message": err.message},
        )
        raise
    except IncompleteQuery as err:
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
