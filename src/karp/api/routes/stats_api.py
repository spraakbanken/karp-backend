import logging
import typing

import pydantic
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from pydantic.json_schema import SkipJsonSchema

from karp import auth
from karp.api import dependencies as deps
from karp.api.params import query_param
from karp.auth.application import resource_permission_queries as resource_permissions
from karp.foundation.value_objects import PermissionLevel
from karp.lex.application import search_queries
from karp.lex.domain.errors import ResourceNotFound
from karp.lex.infrastructure.sql import resource_repository

logger = logging.getLogger(__name__)


router = APIRouter()


class StatisticsDto(pydantic.BaseModel):
    value: str | typing.Any
    count: int


statistics_description = """Return all possible values for `<field>` in `<resource_id>`.

If the field is of type string, the value is not tokens produced by
Opensearch analysis, but the actual value in the data.

Will return an error if there are too many possible values. The limit is
the default settings of `search.max_buckets` in Opensearch which is 65535.
"""


@router.get(
    "/{resource_id}/{field}",
    response_model=typing.List[StatisticsDto],
    description=statistics_description,
)
def get_field_values(
    resource_id: str,
    field: str,
    q: str | SkipJsonSchema[None] = query_param,
    user: auth.User = Depends(deps.get_user_optional),
):
    if not resource_permissions.has_permission(PermissionLevel.read, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    if resource_id not in resource_repository.get_published_resource_ids():
        raise ResourceNotFound(resource_id)
    logger.debug(f"calling statistics ... from {search_queries=}")
    return search_queries.statistics(resource_id, field, q)
