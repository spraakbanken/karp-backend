import logging

try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points

from karp.application import ctx
from karp.application import config

from karp.domain.models.search_service import SearchService

from karp.infrastructure.sql.sql_resource_repository import SqlResourceRepository


logger = logging.getLogger("karp")


def init_context():
    load_infrastructure()

    ctx.resource_repo = SqlResourceRepository()
    ctx.search_service = SearchService.create(config.SEARCH_CONTEXT)


def load_infrastructure():
    for ep in entry_points()["karp.infrastructure"]:
        logger.info("Loading infrastructure module: %s", ep.name)
        print("Loading infrastructure module: %s" % ep.name)
        ep.load()
