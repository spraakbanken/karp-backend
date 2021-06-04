import enum
import logging
from typing import Dict
import typing

import regex

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from karp.domain import errors, repository

from karp.application import config

from karp.services import unit_of_work
from karp.infrastructure.sql.sql_entry_repository import SqlEntryRepository
from karp.infrastructure.sql.sql_resource_repository import SqlResourceRepository

DUPLICATE_PROG = regex.compile(r"Duplicate entry '(.+)' for key '(\w+)'")

_create_new = object()

logger = logging.getLogger("karp")


class SqlUnitOfWork:  # (unit_of_work.UnitOfWork):
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
        return self

    def _check_state(self, expected_state):
        if self._state != expected_state:
            logger.warning(
                "State conflict. unit_of_work is in state '%s' and not '%s'",
                self._state,
                expected_state,
            )
            # raise RuntimeError(
            #     f"State conflict. unit_of_work is in state '{self._state!s}' and not '{expected_state!s}'"
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

    # def __getattr__(self, name):
    #     return self._repo.__getattribute__(name)


DEFAULT_SESSION_FACTORY = sessionmaker(bind=create_engine(config.DB_URL))


class SqlResourceUnitOfWork(SqlUnitOfWork, unit_of_work.ResourceUnitOfWork):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        super().__init__()
        self.session_factory = session_factory
        self._resources = None

    def __enter__(self):
        self._session = self.session_factory()
        self._resources = SqlResourceRepository(self._session)
        return super().__enter__()

    @property
    def repo(self) -> SqlResourceRepository:
        if self._resources is None:
            raise RuntimeError("No resources")
        return self._resources


class SqlEntryUnitOfWork(
    SqlUnitOfWork,
    unit_of_work.EntryUnitOfWork,
    entry_repository_type="sql_v1",
    is_default=True,
):
    def __init__(
        self,
        repo_settings: Dict,
        resource_config: typing.Dict,
        session_factory=DEFAULT_SESSION_FACTORY,
    ):
        super().__init__()
        self.session_factory = session_factory
        self._entries = None
        self.repo_settings = repo_settings
        self.resource_config = resource_config

    def __enter__(self):
        self._session = self.session_factory()
        self._entries = SqlEntryRepository.from_dict(
            self.repo_settings, self.resource_config, session=self._session
        )
        return super().__enter__()

    @property
    def repo(self) -> SqlEntryRepository:
        if self._entries is None:
            raise RuntimeError("No entries")
        return self._entries

    @classmethod
    def from_dict(cls, settings: typing.Dict, resource_config, **kwargs):
        return cls(repo_settings=settings, resource_config=resource_config, **kwargs)

    def collect_new_events(self) -> typing.Iterable:
        if self._entries:
            return super().collect_new_events()
        else:
            return []


class SqlIndexUnitOfWork(unit_of_work.IndexUnitOfWork, index_type="sql_index"):
    @classmethod
    def from_dict(cls, **kwargs):
        print(f"SqlIndexUnitOfWork.from_dict: kwargs = {kwargs}")
        return cls()

    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        self.session_factory = session_factory
        self._index = None

    def _commit(self):
        pass

    def rollback(self):
        pass

    @property
    def repo(self):
        if not self._index:
            raise RuntimeError()
        return self._index


# @unit_of_work.create_entry_unit_of_work.register(SqlEntryRepository)
# def _()
