"""Base class for SQL repositories."""
import logging

from sqlalchemy.orm import Session

logger = logging.getLogger("karp")


class SqlRepository:  # noqa: D101
    def __init__(self, session: Session) -> None:  # noqa: D107
        self._session: Session = session

    def set_session(self, session):  # noqa: ANN201, D102, ANN001
        self._session = session

    def unset_session(self):  # noqa: ANN201, D102
        self._session = None

    def _check_has_session(self):  # noqa: ANN202
        if self._session is None:
            raise RuntimeError("No session, use with unit_of_work.")
