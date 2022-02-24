import logging
from os import stat
import traceback
import sys
import time

try:
    from importlib.metadata import entry_points
except ImportError:
    # used if python < 3.8
    from importlib_metadata import entry_points  # type: ignore

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import injector
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session
import structlog

from karp import main
from karp.foundation import errors as foundation_errors
from karp.foundation.value_objects import unique_id
from karp.auth import errors as auth_errors
from karp.lex.domain import errors as lex_errors
from karp.errors import ClientErrorCodes
from karp.main.modules import RequestScope
from karp.webapp.routes import router as api_router
from karp.webapp import tasks


__version__ = "6.0.2"


tags_metadata = [
    {"name": "Querying", "description": "Query"},
    {"name": "Editing"},
    {"name": "Statistics"},
    {"name": "History"},
    {"name": "Resources"},
    {"name": "Health"},
]

logger = structlog.get_logger()


def create_app(*, with_context: bool = True) -> FastAPI:

    app_context = main.bootstrap_app()

    app = FastAPI(
        title="Karp API",
        redoc_url="/",
        version=__version__,
        openapi_tags=tags_metadata
    )

    app.state.app_context = app_context

    app.add_event_handler(
        "startup",
        tasks.create_start_app_handler(app))
    app.add_event_handler(
        "shutdown",
        tasks.create_stop_app_handler(app)
    )

    main.install_auth_service(
        app_context.container, app_context.settings)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_context.settings.get('web.cors.origins', ['*']),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

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
        raise exc
        return JSONResponse(
            status_code=404,
            content={
                'detail': str(exc),
                'type': str(type(exc)),
            }
        )

    @app.exception_handler(auth_errors.ResourceNotFound)
    async def _auth_entity_not_found(request: Request, exc: auth_errors.ResourceNotFound):
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
        def request_configuration(conn: Connection, session: Session):
            def configure_request_container(binder):
                binder.bind(Connection, to=injector.InstanceProvider(conn))
                binder.bind(Session, to=injector.InstanceProvider(session))

            return configure_request_container
        response = JSONResponse(
            status_code=500,
            content={
                'detail': 'Internal server error'
            }
        )
        try:
            request.state.connection = app_context.container.get(Connection)
            request.state.session = Session(bind=request.state.connection)
            request.state.container = app_context.container.create_child_injector(
                request_configuration(
                    conn=request.state.connection,
                    session=request.state.session,
                ))

            response = await call_next(request)
        finally:
            request.state.connection.close()

        return response

    @app.middleware("http")
    async def logging_middleware(request: Request, call_next) -> Response:
        # clear the threadlocal context
        structlog.threadlocal.clear_threadlocal()
        # bind threadlocal
        structlog.threadlocal.bind_threadlocal(
            # logger="karp",
            request_id=str(unique_id.make_unique_id()),
            cookies=request.cookies,
            scope=request.scope,
            url=str(request.url),
        )
        response = JSONResponse(
            status_code=500,
            content={
                'detail': 'Internal server error'
            }
        )
        start_time = time.time()
        try:
            response: Response = await call_next(request)
        finally:
            process_time = time.time() - start_time
            logger.info(
                "processed a request",
                status_code=response.status_code,
                process_time=process_time,
            )
        return response

    return app


def load_modules(app=None):
    # logger = logging.getLogger("karp")

    if sys.version_info.minor < 10:
        karp_modules = entry_points().get('karp.modules')
    else:
        karp_modules = entry_points(group='karp.modules')
    if karp_modules:
        for ep in karp_modules:
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
