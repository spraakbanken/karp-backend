from typing import Callable, Type
from fastapi import Depends
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session
from starlette.requests import Request

from karp.db_infrastructure import Database

from karp.lex_infrastructure import SqlResourceUnitOfWork
from karp.lex_infrastructure.repositories import SqlResourceRepository


def get_database(request: Request) -> Database:
    return request.app.state.db


def get_session(request: Request) -> Session:
    return request.state.session


def get_connection(request: Request) -> Connection:
    return request.state.connection
