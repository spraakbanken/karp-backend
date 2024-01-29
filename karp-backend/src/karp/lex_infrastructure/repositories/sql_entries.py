"""SQL repositories for entries."""
import logging  # noqa: I001
import typing
from typing import Dict, List, Optional, Generic, Tuple, TypeVar
from attr import has  # noqa: F401

import injector
import regex
import sqlalchemy as sa
from sqlalchemy import func as sa_func

from sqlalchemy import (
    sql,
    exc,
)
from sqlalchemy.orm.session import Session, sessionmaker
from sqlalchemy.sql import insert


import ulid

from karp.foundation.repository import Repository
from karp.lex_core.value_objects import UniqueId
from karp.foundation.events import EventBus
from karp.lex.domain import errors
from karp.lex.application import repositories
from karp.lex.domain.events import Event

from karp.lex.domain.entities.entry import (
    Entry,
    EntryOp,  # noqa: F401
    EntryStatus,  # noqa: F401
)
from karp.lex_infrastructure.sql import sql_models
from karp.db_infrastructure.sql_repository import SqlRepository
from karp.db_infrastructure.sql_unit_of_work import SqlUnitOfWork

logger = logging.getLogger(__name__)


class SqlEntryRepository(SqlRepository, Repository):  # noqa: D101
    def __init__(  # noqa: D107, ANN204
        self,
        history_model,
        resource_config: Dict,
        *,
        session: Session,
    ):
        if not session:
            raise TypeError("session can't be None")
        SqlRepository.__init__(self, session=session)
        self.history_model = history_model
        self.resource_config = resource_config

    @classmethod
    def from_dict(  # noqa: ANN206, D102
        cls,
        name: str,
        resource_config: typing.Dict,
        *,
        session: Session,
    ):
        if not session:
            raise TypeError("session can't be None")
        table_name = name

        logger.info({"table_name": table_name})
        history_model = sql_models.get_or_create_entry_history_model(table_name)

        if session:
            history_model.__table__.create(  # type:ignore [attr-defined]
                bind=session.connection(), checkfirst=True
            )

        return cls(
            history_model=history_model,
            resource_config=resource_config,
            session=session,
        )

    def _save(self, entry: Entry):  # noqa: ANN202
        self._check_has_session()

        return self._insert_history(entry)

    def _insert_history(self, entry: Entry):  # noqa: ANN202
        self._check_has_session()
        try:
            ins_stmt = insert(self.history_model)
            history_dict = self._entry_to_history_dict(entry)
            ins_stmt = ins_stmt.values(**history_dict)
            result = self._session.execute(ins_stmt)
            return result.lastrowid or result.returned_defaults["history_id"]  # type: ignore [attr-defined]
        except exc.DBAPIError as exc:
            raise errors.RepositoryError("db failure") from exc

    def entity_ids(self) -> List[str]:  # noqa: D102
        stmt = self._stmt_latest_not_discarded()
        stmt = stmt.order_by(self.history_model.last_modified.desc())
        query = self._session.execute(stmt).scalars()
        # query = self._session.query(self.history_model).filter_by(discarded=False)
        return [row.entity_id for row in query.all()]

    def by_id(  # noqa: D102
        self,
        id_: UniqueId,
        *,
        version: Optional[int] = None,
        after_date: Optional[float] = None,
        before_date: Optional[float] = None,
        oldest_first: bool = False,
        **kwargs,  # noqa: ANN003
    ):
        if entry := self._by_id(
            id_,
            version=version,
            after_date=after_date,
            before_date=before_date,
            oldest_first=oldest_first,
        ):
            return entry
        raise errors.EntryNotFound(id_=id_)

    def _by_id(
        self,
        id: str,  # noqa: A002
        *,
        version: Optional[int] = None,
        after_date: Optional[float] = None,
        before_date: Optional[float] = None,
        oldest_first: bool = False,
    ) -> Optional[Entry]:
        self._check_has_session()
        query = self._session.query(self.history_model)
        query = query.filter_by(entity_id=id)
        if version:
            query = query.filter_by(version=version)
        elif after_date is not None:
            query = query.filter(self.history_model.last_modified >= after_date).order_by(
                self.history_model.last_modified
            )
        elif before_date:
            query = query.filter(self.history_model.last_modified <= before_date).order_by(
                self.history_model.last_modified.desc()
            )
        elif oldest_first:
            query = query.order_by(self.history_model.last_modified)
        else:
            query = query.order_by(self.history_model.last_modified.desc())
        row = query.first()
        return self._history_row_to_entry(row) if row else None

    def teardown(self):  # noqa: ANN201
        """Use for testing purpose."""
        logger.info("starting teardown")

        logger.info("droping history_model ...")
        self.history_model.__table__.drop(bind=self._session.connection())
        logger.info("dropped history_model")

    def all_entries(self) -> typing.Iterable[Entry]:  # noqa: D102
        stmt = self._stmt_latest_not_discarded()
        query = self._session.execute(stmt).scalars()

        return [self._history_row_to_entry(db_entry) for db_entry in query.all()]

    # TODO Rename this here and in `entity_ids` and `all_entries`
    def _stmt_latest_not_discarded(self):  # noqa: ANN202
        self._check_has_session()
        subq = self._subq_for_latest()
        return sql.select(self.history_model).join(
            subq,
            sa.and_(
                self.history_model.entity_id == subq.c.entity_id,
                self.history_model.last_modified == subq.c.maxdate,
                self.history_model.discarded == False,  # noqa: E712
            ),
        )

    def _subq_for_latest(self) -> sql.Subquery:
        return (
            sql.select(
                self.history_model.entity_id,
                sa.func.max(self.history_model.last_modified).label("maxdate"),
            )
            .group_by(self.history_model.entity_id)
            .subquery("t2")
        )

    def get_history(  # noqa: ANN201, D102
        self,
        user_id: Optional[str] = None,
        entry_id: Optional[str] = None,
        from_date: Optional[float] = None,
        to_date: Optional[float] = None,
        from_version: Optional[int] = None,
        to_version: Optional[int] = None,
        offset: int = 0,
        limit: int = 100,
    ):
        self._check_has_session()
        query = self._session.query(self.history_model)
        if user_id:
            query = query.filter_by(last_modified_by=user_id)
        if entry_id:
            query = query.filter_by(entity_id=entry_id)
        if entry_id and from_version:
            query = query.filter(self.history_model.version >= from_version)
        elif from_date is not None:
            query = query.filter(self.history_model.last_modified >= from_date)
        if entry_id and to_version:
            query = query.filter(self.history_model.version < to_version)
        elif to_date is not None:
            query = query.filter(self.history_model.last_modified <= to_date)

        paged_query = query.order_by(self.history_model.last_modified.desc())
        paged_query = paged_query.limit(limit).offset(offset)

        total = query.count()
        return [self._history_row_to_entry(row) for row in paged_query.all()], total

    def _entry_to_history_dict(self, entry: Entry, history_id: Optional[int] = None) -> Dict:
        return {
            "history_id": history_id,
            "entity_id": entry.id,
            "version": entry.version,
            "last_modified": entry.last_modified,
            "last_modified_by": entry.last_modified_by,
            "body": entry.body,
            "status": entry.status,
            "message": entry.message,
            "op": entry.op,
            "discarded": entry.discarded,
            "repo_id": entry.repo_id,
        }

    def _history_row_to_entry(self, row) -> Entry:
        return Entry(
            body=row.body,
            message=row.message,
            status=row.status,
            op=row.op,
            id=row.entity_id,
            last_modified=row.last_modified,
            last_modified_by=row.last_modified_by,
            discarded=row.discarded,
            version=row.version,
            repository_id=row.repo_id,
        )


class SqlEntryUnitOfWork(  # noqa: D101
    SqlUnitOfWork,
    repositories.EntryUnitOfWork,
):
    def __init__(  # noqa: D107, ANN204
        self,
        session: Session,
        event_bus: EventBus,
        **kwargs,  # noqa: ANN003
    ):
        SqlUnitOfWork.__init__(self)
        if not hasattr(self, "__enter__"):
            raise RuntimeError(f"No __enter__ detected in {self=}")
        repositories.EntryUnitOfWork.__init__(self, event_bus=event_bus, **kwargs)
        self._entries = None
        self._session = session

    # A constructor-ish class method that changes the parameters slightly (e.g.
    # see the line last_modified_by=user below).
    @classmethod
    def create(
        cls,
        session: Session,
        event_bus: EventBus,
        id: UniqueId,  # noqa: A002
        name: str,
        config: Dict,
        connection_str: Optional[str],
        user: str,
        message: str,
        timestamp: float
    ) -> 'SqlEntryUnitOfWork':
        return cls(
            id=id,
            name=name,
            config=config,
            connection_str=connection_str,
            last_modified_by=user,
            message=message,
            last_modified=timestamp,
            session=session,
            event_bus=event_bus,
        )

    def _begin(self):  # noqa: ANN202
        if self._entries is None:
            self._entries = SqlEntryRepository.from_dict(
                name=self.table_name(),
                resource_config=self.config,
                session=self._session,
            )
        return self

    def table_name(self) -> str:  # noqa: D102
        u = ulid.from_uuid(self.entity_id)
        random_part = u.randomness().str
        return f"{self.name}_{random_part}"

    @property
    def repo(self) -> SqlEntryRepository:  # noqa: D102
        if self._entries is None:
            raise RuntimeError("No entries")
        return self._entries

    @classmethod
    def from_dict(  # noqa: ANN206, D102
        cls,
        settings: typing.Dict,
        resource_config,
        **kwargs,  # noqa: ANN003
    ):
        return cls(repo_settings=settings, resource_config=resource_config, **kwargs)

    def collect_new_events(self) -> typing.Iterable:  # noqa: D102
        return super().collect_new_events() if self._entries else []
