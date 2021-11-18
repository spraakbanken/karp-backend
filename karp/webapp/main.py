import logging
from os import stat
import traceback

from karp.errors import ClientErrorCodes

try:
    from importlib.metadata import entry_points
except ImportError:
    # used if python < 3.8
    from importlib_metadata import entry_points  # type: ignore

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import injector

from karp import main
from karp.auth_infrastructure import AuthInfrastructure
from karp.lex.domain import errors as lex_errors

from . import app_config

__version__ = "0.8.1"


tags_metadata = [
    {"name": "Querying", "description": "Query"},
    {"name": "Editing"},
    {"name": "Statistics"},
    {"name": "History"},
    {"name": "Resources"},
    {"name": "Health"},
]

logger = logging.getLogger("karp")


def create_app(*, with_context: bool = True) -> FastAPI:
    app = FastAPI(
        title="Karp API", redoc_url="/", version=__version__, openapi_tags=tags_metadata
    )
    # container = WebAppContainer()
    # container.config.auth.type.from_env("AUTH_CONTEXT")
    # container.config.auth.jwt.pubkey_path.from_env("JWT_AUTH_PUBKEY_PATH")
    app_context = main.bootstrap_app()

    load_auth(app_context.container)
    # from karp.application.logger import setup_logging

    # logger = setup_logging()

    # if with_context:
    #     from karp.application.services.contexts import init_context

    #     init_context()
    # container = WebAppContainer(context=app_context.container)

    # container.config.auth.jwt.pubkey_path.from_env("JWT_AUTH_PUBKEY_PATH")

    from . import (entries_api, health_api, history_api, query_api,
                   resources_api, stats_api)

    # container.wire(
    #     modules=[
    #         app_config,
    #         entries_api,
    #         health_api,
    #         history_api,
    #         query_api,
    #         resources_api,
    #         stats_api,
    #     ]
    # )

    entries_api.init_app(app)
    health_api.init_app(app)
    history_api.init_app(app)
    query_api.init_app(app)
    resources_api.init_app(app)
    stats_api.init_app(app)

    app.state.app_context = app_context
    app.state.container = app_context.container

    load_modules(app)

    from karp.errors import KarpError

    @app.exception_handler(KarpError)
    async def _karp_error_handler(request: Request, exc: KarpError):
        logger.exception(exc)
        return JSONResponse(
            status_code=exc.http_return_code,
            content={"error": exc.message, "errorCode": exc.code},
        )

    @app.exception_handler(lex_errors.LexDomainError)
    def _lex_error_handler(request: Request, exc: lex_errors.LexDomainError):
        logger.exception(exc)
        return lex_exc2response(exc)

    @app.middleware('http')
    async def injector_middleware(request: Request, call_next):
        request.state.container = app_context.container
        response = await call_next(request)
        print('request.state.injector.close')
        return response

    return app


def load_auth(container: injector.Injector):
    container.binder.install(AuthInfrastructure())


def load_modules(app=None):
    logger = logging.getLogger("karp")

    if "karp.modules" in entry_points():
        for ep in entry_points()["karp.modules"]:
            logger.info("Loading module: %s", ep.name)
            print("Loading module: %s" % ep.name)
            mod = ep.load()
            if app:
                init_app = getattr(mod, "init_app", None)
                if init_app:
                    init_app(app)


def lex_exc2response(exc: lex_errors.LexDomainError) -> JSONResponse:
    status_code = 503
    content = {"message": "Internal server error"}
    if isinstance(exc, lex_errors.UpdateConflict):
        status_code = 400
        content = {
            "message": str(exc),
            "errorCode": ClientErrorCodes.VERSION_CONFLICT,
        }
    return JSONResponse(
        status_code=status_code,
        content=content,
    )
