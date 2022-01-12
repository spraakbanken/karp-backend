import enum
import logging
import typing
from typing import Dict

import regex
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


DUPLICATE_PROG = regex.compile(r"Duplicate entry '(.+)' for key '(\w+)'")

_create_new = object()

logger = logging.getLogger("karp")


class SqlUnitOfWork:  # (repositories.UnitOfWork):
    class State(enum.Enum):
        initialized = 0
        begun = 1
        committed = 2
        aborted = 3

    def __init__(self):  # , repo, *, session=_create_new):
        # self._repo = repo
        # if session is _create_new:
        #     self._session = db.SessionLocal()
        #     self._session_is_created_here = True
        # else:
        #     self._session = session
        #     self._session_is_created_here = False

        # self._repo.set_session(self._session)
        self._state = SqlUnitOfWork.State.initialized
        self._session = None

    # @property
    # def repo(self):
    #     return self._repo

    def __enter__(self):
        return self.begin()

    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     if exc_type is None:
    #         # self.commit()
    #         if self._session_is_created_here:
    #             self.close()
    #         return False
    #     self.abort()
    #     if self._session_is_created_here:
    #         self.close()
    #     return False  # re-raise

    def begin(self):
        self._check_state(expected_state=SqlUnitOfWork.State.initialized)
        self._state = SqlUnitOfWork.State.begun
        return self._begin()

    def _begin(self):
        return self

    def _check_state(self, expected_state):
        if self._state != expected_state:
            pass
            # logger.warning(
            #     "State conflict. repositories is in state '%s' and not '%s'",
            #     self._state,
            #     expected_state,
            # )
            # raise RuntimeError(
            #     f"State conflict. repositories is in state '{self._state!s}' and not '{expected_state!s}'"
            # )

    def _commit(self):
        self._check_state(expected_state=SqlUnitOfWork.State.begun)
        # try:
        self._session.commit()
        # self._state = SqlUnitOfWork.State.initialized
        # except db.exc.IntegrityError as err:
        #     logger.exception(err)
        #     str_err = str(err)
        #     print(f"str(err) = {str_err}")
        #     if "Duplicate entry" in str_err:
        #         match = DUPLICATE_PROG.search(str_err)
        #         if match:
        #             value = match.group(1)
        #             key = match.group(2)
        #             if key == "PRIMARY":
        #                 key = self.primary_key()
        #         else:
        #             value = "UNKNOWN"
        #             key = "UNKNOWN"
        #         raise errors.IntegrityError(key=key, value=value) from err
        #     raise errors.IntegrityError("Unknown integrity error") from err

    def abort(self):
        self._check_state(expected_state=SqlUnitOfWork.State.begun)
        self._session.rollback()
        self._state = SqlUnitOfWork.State.initialized

    def rollback(self):
        self._check_state(expected_state=SqlUnitOfWork.State.begun)
        self._session.rollback()
        self._state = SqlUnitOfWork.State.initialized

    def close(self):
        self._session.close()