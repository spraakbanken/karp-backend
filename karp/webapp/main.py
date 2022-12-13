import logging
from os import stat
import traceback
import sys
import time
from typing import Any

try:
    from importlib.metadata import entry_points
except ImportError:
    # used if python < 3.8
    from importlib_metadata import entry_points  # type: ignore

from fastapi import FastAPI, Request, Response, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
import injector
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session
import logging
from asgi_correlation_id import CorrelationIdMiddleware
from asgi_correlation_id.context import correlation_id

from karp import main
from karp.foundation import errors as foundation_errors
from karp.foundation.value_objects import unique_id
from karp.auth import errors as auth_errors
from karp.lex.domain import errors as lex_errors
from karp.errors import ClientErrorCodes
from karp.main import modules, config
from karp.webapp.routes import router as api_router
from karp.webapp import tasks
from karp.webapp.contrib import MatomoMiddleware


querying_description = """
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

- `not(<expression1>||<expression2>||...)` Find all entries that doesn't match the expression <expression>.

- `and(<expression1>||<expression2>||...)` Find all entries that matches <expression1> AND <expression2>.

- `or(<expression1>||<expression2>||...)` Find all entries that matches <expression1> OR <expression2>.

### Regular expressions
Always matches complete tokens.

###  Examples
- `not(missing|pos)`
- `and(freergxp|str.*ng||regexp|pos|str.*ng)`
- `and(missing|pos||equals|wf||or|blomma|äpple`
- `and(equals|wf|sitta||not||equals|wf|satt`
"""


tags_metadata = [
    {
        "name": "Querying",
        "description": querying_description,
    },
    {"name": "Editing"},
    {"name": "Statistics"},
    {"name": "History"},
    {"name": "Resources"},
    {"name": "Health"},
]

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:

    app_context = main.bootstrap_app()

    app = FastAPI(
        title=f"{config.PROJECT_NAME} API",
        redoc_url="/",
        version=config.VERSION,
        openapi_tags=tags_metadata,
    )

    app.state.app_context = app_context

    app.add_event_handler("startup", tasks.create_start_app_handler(app))
    app.add_event_handler("shutdown", tasks.create_stop_app_handler(app))

    main.install_auth_service(app_context.container, app_context.settings)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_context.settings.get("web.cors.origins", ["*"]),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    app.include_router(api_router)

    modules.load_modules("karp.webapp", app=app)

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
                "detail": str(exc),
                "type": str(type(exc)),
            },
        )

    @app.exception_handler(auth_errors.ResourceNotFound)
    async def _auth_entity_not_found(
        request: Request, exc: auth_errors.ResourceNotFound
    ):
        return JSONResponse(
            status_code=404,
            content={
                "detail": str(exc),
            },
        )

    @app.exception_handler(lex_errors.LexDomainError)
    def _lex_error_handler(request: Request, exc: lex_errors.LexDomainError):
        logger.exception(exc)
        return lex_exc2response(exc)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return await http_exception_handler(
            request,
            HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
                headers={
                    "X-Request-ID": correlation_id.get() or "",
                    "Access-Control-Expose-Headers": "X-Request-ID",
                },
            ),
        )

    @app.middleware("http")
    async def injector_middleware(request: Request, call_next):

        response: Response = JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
        try:
            request.state.connection = app_context.container.get(Connection)
            request.state.session = Session(bind=request.state.connection)
            request.state.container = app_context.container.create_child_injector(
                modules.request_configuration(
                    conn=request.state.connection,
                    session=request.state.session,
                )
            )

            response = await call_next(request)
        finally:
            connection = getattr(request.state, "connection", None)
            if connection:
                request.state.connection.close()

        return response

    @app.middleware("http")
    async def _logging_middleware(request: Request, call_next) -> Response:
        response: Response = JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
        start_time = time.time()
        try:
            response = await call_next(request)
        finally:
            process_time = time.time() - start_time
            logger.info(
                "processed a request",
                extra={
                    "status_code": response.status_code,
                    "process_time": process_time,
                },
            )
        return response

    if app_context.settings["tracking.matomo.url"]:
        app.add_middleware(
            MatomoMiddleware,
            idsite=app_context.settings["tracking.matomo.idsite"],
            matomo_url=app_context.settings["tracking.matomo.url"],
            access_token=app_context.settings["tracking.matomo.token"],
        )
    else:
        logger.warning(
            "Tracking to Matomo is not enabled, please set TRACKING_MATOMO_URL."
        )
    app.add_middleware(CorrelationIdMiddleware)

    return app


def lex_exc2response(exc: lex_errors.LexDomainError) -> JSONResponse:
    status_code = 503
    content: dict[str, Any] = {"message": "Internal server error"}
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
