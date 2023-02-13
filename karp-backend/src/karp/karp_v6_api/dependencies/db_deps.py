from typing import Callable, Type  # noqa: F401
from fastapi import Depends  # noqa: F401
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session
from starlette.requests import Request

from karp.db_infrastructure import Database

from karp.lex_infrastructure import SqlResourceUnitOfWork  # noqa: F401
from karp.lex_infrastructure.repositories import SqlResourceRepository  # noqa: F401


def get_database(request: Request) -> Database:
    return request.app.state.db


def get_session(request: Request) -> Session:
    return request.state.session


def get_connection(request: Request) -> Connection:
    return request.state.connection
