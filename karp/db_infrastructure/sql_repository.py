"""Base class for SQL repositories."""
import logging

from sqlalchemy.orm import Session

logger = logging.getLogger("karp")


class SqlRepository:
    def __init__(self, session: Session) -> None:
        self._session: Session = session

    def set_session(self, session):
        self._session = session

    def unset_session(self):
        self._session = None

    def _check_has_session(self):
        if self._session is None:
            raise RuntimeError("No session, use with unit_of_work.")
