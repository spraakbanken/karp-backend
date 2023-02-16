from karp.db_infrastructure import Database  # noqa: D100
from karp.lex_infrastructure import SqlResourceUnitOfWork  # noqa: F401
from karp.lex_infrastructure.repositories import SqlResourceRepository  # noqa: F401
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session
from starlette.requests import Request


def get_database(request: Request) -> Database:  # noqa: D103
    return request.app.state.db


def get_session(request: Request) -> Session:  # noqa: D103
    return request.state.session


def get_connection(request: Request) -> Connection:  # noqa: D103
    return request.state.connection
