import logging

try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points  # type: ignore

# from karp.application import ctx
# from karp.application import config
from karp.domain import events
from karp.services import context

# from karp.domain.models.search_service import SearchService

# from karp.infrastructure.sql.sql_resource_repository import SqlResourceRepository
# from karp.infrastructure.testing.dummy_auth_service import DummyAuthService
# from karp.infrastructure.jwt.jwt_auth_service import JWTAuthenticator


logger = logging.getLogger("karp")


# def init_context():
#     load_infrastructure()

#     ctx.resource_repo = SqlResourceRepository()
#     ctx.search_service = SearchService.create(config.SEARCH_CONTEXT)
#     if config.DEBUG or config.TESTING:
#         logger.warn("Running in DEBUG mode")
#         ctx.auth_service = DummyAuthService()
#     else:
#         ctx.auth_service = JWTAuthenticator()


def load_infrastructure(evt: events.AppStarted, ctx: context.Context):
    print("load_infrastructure")
    for ep in entry_points()["karp.infrastructure"]:
        logger.info("Loading infrastructure module: %s", ep.name)
        print("Loading infrastructure module: %s" % ep.name)
        ep.load()
