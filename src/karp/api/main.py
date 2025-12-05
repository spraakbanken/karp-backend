import io
import logging
import traceback
from contextlib import redirect_stdout
from typing import Any

from asgi_correlation_id import CorrelationIdMiddleware
from asgi_correlation_id.context import correlation_id
from asgi_matomo import MatomoMiddleware
from fastapi import FastAPI, HTTPException, Request, Response, status  # noqa: I001
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from karp import main
from karp.api.routes import router as api_router
from karp.auth import errors as auth_errors
from karp.foundation import errors as foundation_errors
from karp.lex.application.resource_queries import ResourceQueries
from karp.lex.domain import errors as lex_errors
from karp.main import config, new_session
from karp.main.app import with_new_session
from karp.main.errors import ClientErrorCodes, UserError
from karp.plugins.plugin import Plugins

searching_description = """
Searching is the main way to get data from Karp. If a query string is given, an actual search will be done, otherwise all
entries in the resource will be returned.

- Use [`/query`](#tag/Searching/operation/query_query__resources__get) to be given all the matching entries
- Use [`/query/stats`](#tag/Searching/operation/query_stats_query_stats__resources__get) to only be given the count of matches in each given resource

### Query language

#### Search strings

In the examples below, `<string>` can be either:

- any characters except `"`, `|`, `(` or `)`
- any characters, enclosed in double quotes, but any `"` inside the quotes must be escaped with `\`, for example: `equals|field|"A \"good\" example"`

In addition to these rules, characters that are part of the URI syntax, such as `?` and `&` needs to be encoded. For example, the whole query can be
encoded using Javascript's `encodeURIComponent`.

#### Query operators

- `contains|<field>|<string>` Find all entries where the field <field> contains <string>. More premissive than equals.

- `endswith|<field>|<string>` Find all entries where the field <field> ends with <string>

- `equals|<field>|<string>` Find all entries where <field> equals <string>. Stricter than contains

- `exists|<field>` Find all entries that has the field <field>.

- `freetext|<string>` Search in all fields for <string> and similar values.

- `gt|<field>|<value>` Find all entries where <field> is greater than <value>.

- `gte|<field>|<value>` Find all entries where <field> is greater than or equals <value>.

- `lt|<field>|<value>` Find all entries where <field> is less than <value>.

- `lte|<field>|<value>` Find all entries where <field> is less than or equals <value>.

- `missing|<field>` Search for all entries that doesn't have the field <field>.

- `regexp|<field>|<regex.*>` Find all entries where the field <field> matches the regex <regex.*>.

- `startswith|<field>|<string>` Find all entries where <field>starts with <string>.

#### Logical Operators
The logical operators can be used both at top-level and lower-levels.

- `not(<expression1>||<expression2>||...)` Find all entries that doesn't match the expression <expression>.

- `and(<expression1>||<expression2>||...)` Find all entries that matches <expression1> AND <expression2>.

- `or(<expression1>||<expression2>||...)` Find all entries that matches <expression1> OR <expression2>.

#### Sub-queries - searching in collections of objects

Used for fields with setting `collection: true` and that contain other fields (collection of objects). Boolean queries
such as: `and(equals|my_field.x|1||equals|my_field.y|3)` will find entries where objects in `my_field` 
match `equals|x|1` or `equals|y|3`, or both. To find entries where an individual object in `my_field` matches a boolean query, 
wrap the query with the sub-query notation: `my_field(and(equals|x|1||equals|y|3))`.

- `<field>(expression)` Do `<expression>` on objects inside `<field>`. `<field>` must be a collection. 

#### Regular expressions
Always matches complete tokens.

####  Examples
- `not(missing|pos)`
- `and(freergxp|str.*ng||regexp|pos|str.*ng)`
- `and(missing|pos||equals|wf||or|blomma|äpple`
- `and(equals|wf|sitta||not||equals|wf|satt`
"""


tags_metadata = [
    {
        "name": "Searching",
        "description": searching_description,
    },
    {"name": "Editing"},
    {"name": "Statistics"},
    {"name": "History"},
    {"name": "Resources"},
]

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app_context = main.bootstrap_app()

    app = FastAPI(
        title=f"{config.PROJECT_NAME} API",
        description="""Karp is Språkbanken's tool for editing structural data.\n\nThe
        main goal of Karp is to be great for working with **lexical** data, but will work with 
        other data as well.\n\n[Read more here](https://github.com/spraakbanken/karp-backend/blob/release/docs/index.md)""",
        redoc_url=None,
        docs_url=None,
        version=config.VERSION,
        openapi_tags=tags_metadata,
    )

    app.state.app_context = app_context

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_context.settings.get("web.cors.origins", ["*"]),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # add all plugin API routes
    plugins = app_context.injector.get(Plugins)
    resource_queries = with_new_session(app_context.injector).get(ResourceQueries)
    plugin_routes_added = plugins.register_routes(resource_queries.get_published_resources())

    if plugin_routes_added:
        app.openapi_tags.append(
            {
                "name": "Plugins",
                "description": "API calls here are not part of Karp's basic functionality and may be tailored for a specific resource.",
            }
        )

    app.include_router(api_router)

    from karp.main.errors import KarpError

    @app.exception_handler(KarpError)
    async def _karp_error_handler(request: Request, exc: KarpError):
        logger.exception(exc)
        return JSONResponse(
            status_code=exc.http_return_code,
            content={"error": exc.message, "errorCode": exc.code},
        )

    @app.exception_handler(UserError)
    async def _user_error_handler(request: Request, exc: UserError):
        # Don't log exceptions from UserError
        return JSONResponse(status_code=400, content=exc.to_dict())

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
    async def _auth_entity_not_found(request: Request, exc: auth_errors.ResourceNotFound):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": str(exc),
            },
        )

    @app.exception_handler(lex_errors.ResourceNotFound)
    async def _resource_not_found_handler(request, exc):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": "One of the given resources do not exist.",
            },
        )

    @app.exception_handler(lex_errors.LexDomainError)
    def _lex_error_handler(request: Request, exc: lex_errors.LexDomainError):
        logger.exception(exc)
        return lex_exc2response(exc)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        def extract_exceptions(excs):
            output = []
            for inner_exc in excs:
                if hasattr(inner_exc, "exceptions"):
                    output.extend(extract_exceptions(inner_exc.exceptions))
                else:
                    output.append(inner_exc)
            return output

        for out_exc in extract_exceptions([exc]):
            traceback.print_exception(out_exc)
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
        response: Response = JSONResponse(status_code=500, content={"detail": "Internal server error"})
        # Create a new session per request
        with new_session(app_context.injector) as injector:
            request.state.session = injector.get(Session)
            request.state.injector = injector

            response = await call_next(request)

        return response

    @app.middleware("http")
    async def _logging_middleware(request: Request, call_next) -> Response:
        response: Response | None = None
        try:
            response = await call_next(request)
        finally:
            if not response:
                response = JSONResponse(status_code=500, content={"detail": "Internal server error"})
        return response

    if app_context.settings["tracking.matomo.url"]:

        class MatomoAdapterMiddleware(MatomoMiddleware):
            """
            Silence printouts from MatomoMiddleware
            """

            async def startup(self) -> None:
                with redirect_stdout(io.StringIO()):
                    await super().startup()

            async def shutdown(self) -> None:
                with redirect_stdout(io.StringIO()):
                    await super().shutdown()

        app.add_middleware(
            MatomoAdapterMiddleware,
            idsite=app_context.settings["tracking.matomo.idsite"],
            matomo_url=app_context.settings["tracking.matomo.url"],
            access_token=app_context.settings["tracking.matomo.token"],
        )
    else:
        logger.warning("Tracking to Matomo is not enabled, please set TRACKING_MATOMO_URL.")
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
