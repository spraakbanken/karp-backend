from typing import Callable, Type
from fastapi import Depends
from sqlalchemy.orm import Session
from starlette.requests import Request

from karp.db_infrastructure import Database
from karp.db_infrastructure.base_repository import BaseRepository

from karp.lex_infrastructure import SqlResourceUnitOfWork
from karp.lex_infrastructure.repositories import SqlResourceRepository


def get_database(request: Request) -> Database:
    return request.app.state.db


def get_session(db: Database = Depends(get_database)) -> Session:
    try:
        db_session = db.session_factory()
        yield db_session
    finally:
        db_session.close()


def get_repository(Repo_type: Type[BaseRepository]) -> Callable:
    def get_repo(db: Database = Depends(get_database)) -> Type[BaseRepository]:
        return Repo_type(db)
    return get_repo


def get_resource_repository(db_session: Session = Depends(get_session)) -> SqlResourceRepository:
    return SqlResourceRepository(db_session)


def get_resource_unit_of_work(db: Database = Depends(get_database)) -> SqlResourceUnitOfWork:
    return SqlResourceUnitOfWork(db.session_factory)
