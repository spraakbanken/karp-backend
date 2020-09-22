"""Base class for SQL repositories."""
from enum import Enum
from typing import Optional

from karp.infrastructure import unit_of_work
from karp.infrastructure.sql import db


class SqlRepository:
    def __init__(self) -> None:
        self._session: Optional[db.Session] = None

    def set_session(self, session):
        self._session = session

    def unset_session(self):
        self._session = None

    def _check_has_session(self):
        if self._session is None:
            raise RuntimeError("No session, use with unit_of_work.")


_create_new = object()


@unit_of_work.create_unit_of_work.register(SqlRepository)
def _(repo: SqlRepository, *, session=_create_new):
    return SqlUnitOfWork(repo, session=session)


class SqlUnitOfWork:
    class State(Enum):
        initialized = 0
        begun = 1
        committed = 2
        aborted = 3

    def __init__(self, repo, *, session=_create_new):
        self._repo = repo
        if session is _create_new:
            self._session = db.SessionLocal()
            self._session_is_created_here = True
        else:
            self._session = session
            self._session_is_created_here = False

        self._repo.set_session(self._session)
        self._state = SqlUnitOfWork.State.initialized

    def __enter__(self):
        return self.begin()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
            if self._session_is_created_here:
                self.close()
            return False
        self.abort()
        if self._session_is_created_here:
            self.close()
        return False  # re-raise

    def begin(self):
        self._check_state(expected_state=SqlUnitOfWork.State.initialized)
        self._state = SqlUnitOfWork.State.begun
        return self

    def _check_state(self, expected_state):
        if self._state != expected_state:
            raise RuntimeError(
                f"State conflict. unit_of_work is in state '{self._state!s}' and not '{expected_state!s}'"
            )

    def commit(self):
        self._check_state(expected_state=SqlUnitOfWork.State.begun)
        self._session.commit()

    def abort(self):
        self._check_state(expected_state=SqlUnitOfWork.State.begun)
        self._session.rollback()

    def close(self):
        self._session.close()

    def __getattr__(self, name):
        return self._repo.__getattribute__(name)
