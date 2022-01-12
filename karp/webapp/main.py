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
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import injector

from karp import main
from karp.foundation import errors as foundation_errors
from karp.auth import errors as auth_errors
from karp.lex.domain import errors as lex_errors

from . import app_config

__version__ = "6.0.0"


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

    main.install_auth_service(
        app_context.container, app_context.settings)
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

    @app.exception_handler(foundation_errors.NotFoundError)
    async def _entity_not_found(request: Request, exc: foundation_errors.NotFoundError):
        return JSONResponse(
            status_code=404,
            content={
                'detail': str(exc),
            }
        )

    @app.exception_handler(auth_errors.ResourceNotFound)
    async def _entity_not_found(request: Request, exc: auth_errors.ResourceNotFound):
        return JSONResponse(
            status_code=404,
            content={
                'detail': str(exc),
            }
        )

    @app.exception_handler(lex_errors.LexDomainError)
    def _lex_error_handler(request: Request, exc: lex_errors.LexDomainError):
        logger.exception(exc)
        return lex_exc2response(exc)

    @app.middleware('http')
    async def injector_middleware(request: Request, call_next):
        request.state.container = app_context.container
        response = await call_next(request)
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_context.settings.get('web.cors.origins', '*')
    )
    return app


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
