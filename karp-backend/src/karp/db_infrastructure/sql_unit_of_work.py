import enum  # noqa: D100, I001
import logging
import typing  # noqa: F401
from typing import Dict, Optional  # noqa: F401

from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


class SqlUnitOfWork:  # noqa: D101
    class State(enum.Enum):  # noqa: D106
        initialized = 0
        begun = 1
        committed = 2
        aborted = 3

    def __init__(  # noqa: D107, ANN204
        self,
        *,
        session: Optional[Session] = None,
    ):
        logger.debug("Init sqlunitofwork session=%s", session)

        self._session = session
        self._session_is_created_here = self._session is None
        self._state = SqlUnitOfWork.State.initialized

    def begin(self):  # noqa: ANN201, D102
        self._state = SqlUnitOfWork.State.begun
        return self._begin()

    def _begin(self):  # noqa: ANN202
        return self

    def _commit(self):  # noqa: ANN202
        logger.info(
            "About to commit",
            extra={
                "session": self._session,
                "session_new": self._session.new if self._session else None,
            },
        )
        self._session.commit()
        logger.info(
            "commited",
            extra={
                "session": self._session,
                "session_new": self._session.new if self._session else None,
            },
        )

    def abort(self):  # noqa: ANN201, D102
        self._session.rollback()
        self._state = SqlUnitOfWork.State.initialized

    def rollback(self):  # noqa: ANN201, D102
        logger.debug("rollback called")
        self._session.rollback()
        self._state = SqlUnitOfWork.State.initialized

    def _close(self):  # noqa: ANN202
        if self._session_is_created_here:
            logger.debug("closing session=%s", self._session)
            self._session.close()
