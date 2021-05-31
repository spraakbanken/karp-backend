"""Base class for SQL repositories."""
from enum import Enum
import logging
from typing import Optional

import regex

from karp import errors

from karp.services import unit_of_work
from karp.infrastructure.sql import db


logger = logging.getLogger("karp")


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


# @unit_of_work.create_unit_of_work.register(SqlRepository)
# def _(repo: SqlRepository, *, session=_create_new):
#     return SqlUnitOfWork(repo, session=session)
