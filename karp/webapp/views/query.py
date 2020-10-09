"""
Query API.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Security, HTTPException, status, Query, Path

from karp import errors

from karp.domain.models.user import User
from karp.domain.models.auth_service import PermissionLevel

from karp.application import ctx
from karp.application.services import resources as resources_service

from karp.webapp import schemas
from karp.webapp.auth import get_current_user


_logger = logging.getLogger("karp")


router = APIRouter()


@router.get("/entries/{resource_id}/{entry_ids}")
def get_entries_by_id(
    resource_id: str,
    entry_ids: str,
    user: User = Security(get_current_user, scopes=["read"]),
):
    print("webapp.views.get_entries_by_id")
    if not ctx.auth_service.authorize(PermissionLevel.read, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="read"'},
        )
    return ctx.search_service.search_ids(resource_id, entry_ids)


# @router.get("/{resources}/query")
@router.get("/query/{resources}")
def query(
    resources: str = Path(...),  # , regex=r"^\w+(,\w+)*$"),
    q: Optional[str] = Query(None),
    from_: int = Query(0, alias="from"),
    # size: int = Query(25),
    # lexicon_stats: bool = Query(True),
    # include_fields: Optional[List[str]] = Query(None),
    user: User = Security(get_current_user, scopes=["read"]),
):
    print("Called 'query' called with resources={}".format(resources))
    resource_list = resources.split(",")
    if not ctx.auth_service.authorize(PermissionLevel.read, user, resource_list):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="read"'},
        )
    resources_service.check_resource_published(resource_list)
    try:
        args = {
            "from": from_,
        }
        q = ctx.search_service.build_query(args, resources)
        print("query::q={q}".format(q=q))
        response = ctx.search_service.search_with_query(q)
    except errors.KarpError as e:
        _logger.exception(
            "Error occured when calling 'query' with resources='{}' and q='{}'. e.msg='{}".format(
                resources, q, e.message
            )
        )
        raise
    return response


# @router.get("/{resources}/query_split")
# @router.get("/query_split/{resources}")
# def query_split(
#     resources: str,
#     user: User = Security(get_current_user, scopes=["read"]),
# ):
#     print("query_split called with resources={}".format(resources))
#     if not ctx.auth_service.authorize(PermissionLevel.read, user, [resource_id]):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Not enough permissions",
#             headers={"WWW-Authenticate": 'Bearer scope="read"'},
#         )
#     resource_list = resources.split(",")
#     resourcemgr.check_resource_published(resource_list)
#     try:
#         query = search.build_query(request.args, resources)
#         query.split_results = True
#         print("query={}".format(query))
#         response = search.search_with_query(query)
#     except errors.KarpError as e:
#         _logger.exception(
#             "Error occured when calling 'query' with resources='{}' and q='{}'. msg='{}'".format(
#                 resources, request.args.get("q"), e.message
#             )
#         )
#         raise
#     return flask_jsonify(response), 200


def init_app(app):
    app.include_router(router)
