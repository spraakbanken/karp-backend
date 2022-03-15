"""
Query API.
"""
import logging
from typing import List, Optional

from fastapi import (APIRouter, Depends, HTTPException, Path, Query, Security,
                     status)

from karp import errors as karp_errors, auth, search
from karp.search.application.queries import SearchService, QueryRequest
from karp.webapp import schemas

from karp.webapp import dependencies as deps
from karp.webapp.dependencies.fastapi_injector import inject_from_req


logger = logging.getLogger(__name__)


router = APIRouter()


@router.get(
    "/entries/{resource_id}/{entry_ids}",
    description="Returns a list of entries matching the given ids",
    name="Get lexical entries by id",
)
def get_entries_by_id(
    resource_id: str = Path(...,
                            description="The resource to perform operation on"),
    entry_ids: str = Path(
        ...,
        description="Comma-separated. The ids to perform operation on.",
        regex=r"^\w(,\w)*",
    ),
    user: auth.User = Security(deps.get_user_optional, scopes=["read"]),
    auth_service: auth.AuthService = Depends(deps.get_auth_service),
    search_service: SearchService = Depends(inject_from_req(SearchService)),
):
    logger.debug("webapp.views.get_entries_by_id")
    if not auth_service.authorize(
        auth.PermissionLevel.read, user, [resource_id]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="read"'},
        )
    return search_service.search_ids(resource_id, entry_ids)


@router.get("/split/{resources}", name="Query per resource")
def query_split(
    resources: str = Path(
        ...,
        regex=r"^[a-z_0-9\-]+(,[a-z_0-9\-]+)*$",
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
        regex=r"^[a-zA-Z0-9_\-]+\|(asc|desc)",
    ),
    lexicon_stats: bool = Query(
        True, description="Show the hit count per lexicon"),
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
    user: auth.User = Security(deps.get_user_optional, scopes=["read"]),
    auth_service: auth.AuthService = Depends(deps.get_auth_service),
    search_service: SearchService = Depends(inject_from_req(SearchService)),
):
    logger.debug('/query/split called', extra={'resources': resources})
    resource_list = resources.split(",")
    if not auth_service.authorize(
        auth.PermissionLevel.read, user, resource_list
    ):
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
            extra={'resources': resources,
                   'q': q,
                   'error_message': err.message},
        )
        raise
    except search.IncompleteQuery as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'errorCode': karp_errors.ClientErrorCodes.SEARCH_INCOMPLETE_QUERY,
                'message': 'Error in query',
                'failing_query': err.failing_query,
                'error_description': err.error_description,
            }
        )
    return response


@router.get(
    "/{resources}",
    # summary="Returns a list of entries matching the given query in the given resources. The results are mixed from the given resources.",
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
        description="The query. If missing, all entries in chosen resource(s) will be returned.",
    ),
    from_: int = Query(
        0, alias="from", description="Specify which entry should be the first returned."
    ),
    size: int = Query(25, description="Number of entries in page."),
    sort: List[str] = Query(
        [],
        description="The `field` to sort by. If missing, default order for each resource will be used.",
        regex=r"^[a-zA-Z0-9_\-]+\|(asc|desc)",
    ),
    lexicon_stats: bool = Query(
        True, description="Show the hit count per lexicon"),
    include_fields: Optional[List[str]] = Query(
        None, description="Comma-separated list of which fields to return"
    ),
    exclude_fields: Optional[List[str]] = Query(
        None, description="Comma-separated list of which fields to remove from result"
    ),
    format_: schemas.EntryFormat = Query(
        schemas.EntryFormat.json,
        alias="format",
        description="Will return the result in the specified format.",
    ),
    user: auth.User = Security(deps.get_user_optional, scopes=["read"]),
    auth_service: auth.AuthService = Depends(deps.get_auth_service),
    search_service: SearchService = Depends(inject_from_req(SearchService)),
):
    """
    Returns a list of entries matching the given query in the given resources. The results are mixed from the given resources.

    ## Query DSL
    ### Query operators
    - `contains|<field>|<string>` Find all entries where the field <field> contains <string>. More premissive than equals.

    - `endswith|<field>|<string>` Find all entries where the field <field> ends with <string>

    - `equals|<field>|<string>` Find all entries where <field> equals <string>. Stricter than contains

    - `exists|<field>` Find all entries that has the field <field>.

    - `freetext|<string>` Search in all fields for <string> and similar values.

    - `freergxp|<regex.*>` Search in all fields for the regex <regex.*>.

    - `gt|<field>|<value>` Find all entries where <field> is greater than <value>.

    - `gte|<field>|<value>` Find all entries where <field> is greater than or equals <value>.

    - `lt|<field>|<value>` Find all entries where <field> is less than <value>.

    - `lte|<field>|<value>` Find all entries where <field> is less than or equals <value>.

    - `missing|<field>` Search for all entries that doesn't have the field <field>.

    - `regexp|<field>|<regex.*>` Find all entries where the field <field> matches the regex <regex.*>.

    - `startswith|<field>|<string>` Find all entries where <field>starts with <string>.

    ### Logical Operators
    The logical operators can be used both at top-level and lower-levels.

    - `not(<expression1>||<experssion2>||...)` Find all entries that doesn't match the expression <expression>.

    - `and(<expression1>||<expression2>||...)` Find all entries that matches <expression1> AND <expression2>.

    - `or(<expression1>||<expression2>||...)` Find all entries that matches <expression1> OR <expression2>.

    ### Regular expressions
    Always matches complete tokens.
    """
    # Examples
    # not||missing|pos
    # and||freergxp|str.*ng||regexp|pos|str.*ng
    # and||missing|pos||equals|wf||or|blomma|äpple
    # and||equals|wf|sitta||not||equals|wf|satt
    # """
    logger.debug(
        "Called 'query' called with", extra={'resources': resources, 'from': from_, 'size': size}
    )
    resource_list = resources.split(",")
    if not auth_service.authorize(
        auth.PermissionLevel.read, user, resource_list
    ):
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
        print(f'{search_service=}')
        response = search_service.query(query_request)

    except karp_errors.KarpError as err:
        logger.exception(
            "Error occured when calling 'query' with",
            extra={'resources': resources,
                   'q': q,
                   'error_message': err.message},
        )
        raise
    return response


def init_app(app):
    app.include_router(router)
