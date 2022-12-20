import typing

from fastapi import APIRouter, Depends, HTTPException, Response, Security, status

from karp import auth
from karp.foundation.value_objects import PermissionLevel
from karp.search.application.queries import SearchService, StatisticsDto
from karp.webapp import schemas

from karp.webapp import dependencies as deps
from karp.webapp.dependencies.fastapi_injector import inject_from_req


router = APIRouter()


@router.get(
    "/{resource_id}/{field}",
    response_model=typing.List[StatisticsDto],
)
def get_field_values(
    resource_id: str,
    field: str,
    user: auth.User = Security(deps.get_user_optional, scopes=["read"]),
    auth_service: auth.AuthService = Depends(deps.get_auth_service),
    search_service: SearchService = Depends(inject_from_req(SearchService)),
):
    if not auth_service.authorize(PermissionLevel.read, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="read"'},
        )
    print(f"calling statistics ... from {search_service=}")
    return search_service.statistics(resource_id, field)


def init_app(app):
    app.include_router(router)
