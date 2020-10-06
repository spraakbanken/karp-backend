from karp.application import ctx
from karp.application import config

from karp.domain.models.search_service import SearchService

from karp.infrastructure.sql.sql_resource_repository import SqlResourceRepository


def init_context():

    ctx.resource_repo = SqlResourceRepository()
    ctx.search_service = SearchService.create(config.SEARCH_CONTEXT)
