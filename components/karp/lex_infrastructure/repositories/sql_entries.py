"""SQL repositories for entries."""
import logging
import typing
from typing import Dict, List, Optional, Generic, TypeVar

import injector
import regex
import sqlalchemy as sa
from sqlalchemy import func as sa_func
from sqlalchemy import sql
from sqlalchemy.orm import sessionmaker
import ulid

from karp.foundation.value_objects import UniqueId
from karp.foundation.events import EventBus
from karp.lex.domain import errors
from karp.lex.application import repositories

# from karp.domain.errors import NonExistingField, RepositoryError
from karp.lex.domain.entities.entry import (  # EntryRepositorySettings,; EntryRepository,; create_entry_repository,
    Entry,
    EntryOp,
    EntryStatus,
)
from karp.db_infrastructure import db
from karp.lex_infrastructure.sql import sql_models
from karp.db_infrastructure.sql_repository import SqlRepository
from karp.db_infrastructure.sql_unit_of_work import SqlUnitOfWork

logger = logging.getLogger(__name__)

DUPLICATE_PATTERN = r"Duplicate entry '(.+)' for key '(\w+)'"
DUPLICATE_PROG = regex.compile(DUPLICATE_PATTERN)
NO_PROPERTY_PATTERN = regex.compile(r"has no property '(\w+)'")


class SqlEntryRepository(repositories.EntryRepository, SqlRepository):
    def __init__(
        self,
        history_model,
        resource_config: Dict,
        *,
        session: db.Session,
    ):
        if not session:
            raise TypeError("session can't be None")
        repositories.EntryRepository.__init__(self)
        SqlRepository.__init__(self, session=session)
        self.history_model = history_model
        self.resource_config = resource_config

    @classmethod
    def from_dict(
        cls,
        name: str,
        resource_config: typing.Dict,
        *,
        session: db.Session,
    ):
        if not session:
            raise TypeError("session can't be None")
        table_name = name

        logger.info({"table_name": table_name})
        history_model = sql_models.get_or_create_entry_history_model(table_name)

        if session:
            history_model.__table__.create(  # type:ignore [attr-defined]
                bind=session.bind, checkfirst=True
            )

        return cls(
            history_model=history_model,
            resource_config=resource_config,
            session=session,
        )

    @classmethod
    def _create_repository_settings(
        cls, resource_id: str, resource_config: typing.Dict
    ) -> typing.Dict:
        return {
            "table_name": resource_id,
            "resource_id": resource_id,
        }

    def _save(self, entry: Entry):
        self._check_has_session()

        return self._insert_history(entry)

    def _insert_history(self, entry: Entry):
        self._check_has_session()
        try:
            ins_stmt = db.insert(self.history_model)
            history_dict = self._entry_to_history_dict(entry)
            ins_stmt = ins_stmt.values(**history_dict)
            result = self._session.execute(ins_stmt)
            return result.lastrowid or result.returned_defaults["history_id"]
        except db.exc.DBAPIError as exc:
            raise errors.RepositoryError("db failure") from exc

    def entity_ids(self) -> List[str]:
        stmt = self._stmt_latest_not_discarded()
        stmt = stmt.order_by(self.history_model.last_modified.desc())
        query = self._session.execute(stmt).scalars()
        # query = self._session.query(self.history_model).filter_by(discarded=False)
        return [row.entity_id for row in query.all()]

    def _by_id(
        self,
        id: str,
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
            query = query.filter(
                self.history_model.last_modified >= after_date
            ).order_by(self.history_model.last_modified)
        elif before_date:
            query = query.filter(
                self.history_model.last_modified <= before_date
            ).order_by(self.history_model.last_modified.desc())
        elif oldest_first:
            query = query.order_by(self.history_model.last_modified)
        else:
            query = query.order_by(self.history_model.last_modified.desc())
        row = query.first()
        return self._history_row_to_entry(row) if row else None

    def teardown(self):
        """Use for testing purpose."""
        logger.info("starting teardown")

        logger.info("droping history_model ...")
        self.history_model.__table__.drop(bind=self._session.bind)
        logger.info("dropped history_model")

    def all_entries(self) -> typing.Iterable[Entry]:
        stmt = self._stmt_latest_not_discarded()
        query = self._session.execute(stmt).scalars()

        return [self._history_row_to_entry(db_entry) for db_entry in query.all()]

    # TODO Rename this here and in `entity_ids` and `all_entries`
    def _stmt_latest_not_discarded(self):
        self._check_has_session()
        subq = self._subq_for_latest()
        return sql.select(self.history_model).join(
            subq,
            sa.and_(
                self.history_model.entity_id == subq.c.entity_id,
                self.history_model.last_modified == subq.c.maxdate,
                self.history_model.discarded == False,
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

    def num_entities(self) -> int:
        self._check_has_session()

        subq = self._subq_for_latest()

        stmt = sql.select(sa_func.count(self.history_model.entity_id)).join(
            subq,
            sa.and_(
                self.history_model.entity_id == subq.c.entity_id,
                self.history_model.last_modified == subq.c.maxdate,
                self.history_model.discarded == False,
            ),
        )
        return self._session.execute(stmt).scalar()

    def by_referenceable(self, filters: Optional[Dict] = None, **kwargs) -> List[Entry]:
        self._check_has_session()

        if filters is None:
            if not kwargs:
                raise ValueError("Must give 'filters' or kwargs")
            else:
                filters = kwargs

        subq = self._subq_for_latest()
        query_and = sa.and_(
            self.history_model.entity_id == subq.c.entity_id,
            self.history_model.last_modified == subq.c.maxdate,
            self.history_model.discarded == False,
        )

        for filter_key, filter_value in filters.items():

            query_and = query_and & (
                sa_func.json_extract(self.history_model.body, f"$.{filter_key}")
                == filter_value
            )
        stmt = sql.select(self.history_model).join(
            subq,
            query_and,
        )

        return [
            self._history_row_to_entry(row)
            for row in self._session.execute(stmt).scalars().all()
        ]

    def get_history(
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

        paged_query = query.limit(limit).offset(offset)
        total = query.count()
        return [self._history_row_to_entry(row) for row in paged_query.all()], total

    def _entry_to_history_dict(
        self, entry: Entry, history_id: Optional[int] = None
    ) -> Dict:
        return {
            "history_id": history_id,
            "entity_id": entry.entity_id,
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
            entity_id=row.entity_id,
            last_modified=row.last_modified,
            last_modified_by=row.last_modified_by,
            discarded=row.discarded,
            version=row.version,
            repository_id=row.repo_id,
        )


class SqlEntryUnitOfWork(
    SqlUnitOfWork,
    repositories.EntryUnitOfWork,
):
    repository_type: str = "sql_entries_base"

    def __init__(
        self,
        session_factory: sessionmaker,
        event_bus: EventBus,
        **kwargs,
    ):
        SqlUnitOfWork.__init__(self)
        repositories.EntryUnitOfWork.__init__(self, event_bus=event_bus, **kwargs)
        self.session_factory = session_factory
        self._entries = None
        self._session = None

    def _begin(self):
        if self._session is None:
            self._session = self.session_factory()
        if self._entries is None:
            self._entries = SqlEntryRepository.from_dict(
                name=self.table_name(),
                resource_config=self.config,
                session=self._session,
            )
        return self

    def table_name(self) -> str:
        return self.name

    @property
    def repo(self) -> SqlEntryRepository:
        if self._entries is None:
            raise RuntimeError("No entries")
        return self._entries

    @classmethod
    def from_dict(cls, settings: typing.Dict, resource_config, **kwargs):
        return cls(repo_settings=settings, resource_config=resource_config, **kwargs)

    def collect_new_events(self) -> typing.Iterable:
        return super().collect_new_events() if self._entries else []


class SqlEntryUnitOfWorkV1(SqlEntryUnitOfWork):
    repository_type: str = "sql_entries_v1"


class SqlEntryUnitOfWorkV2(SqlEntryUnitOfWork):
    repository_type: str = "sql_entries_v2"

    def table_name(self) -> str:
        u = ulid.from_uuid(self.entity_id)
        random_part = u.randomness().str
        return f"{self.name}_{random_part}"


SqlEntryUowType = TypeVar("SqlEntryUowType", bound=SqlEntryUnitOfWork)


class SqlEntryUowCreator(Generic[SqlEntryUowType]):
    repository_type: str = "repository_type"

    @injector.inject
    def __init__(
        self,
        session_factory: sessionmaker,
        event_bus: EventBus,
    ):
        self._session_factory = session_factory
        self.event_bus = event_bus
        self.cache = {}

    def _create_uow(self, **kwargs) -> SqlEntryUowType:
        raise NotImplementedError(f"please implement this for {self}")

    def __call__(
        self,
        entity_id: UniqueId,
        name: str,
        config: Dict,
        connection_str: Optional[str],
        user: str,
        message: str,
        timestamp: float,
    ) -> SqlEntryUowType:
        if entity_id not in self.cache:
            self.cache[entity_id] = self._create_uow(
                entity_id=entity_id,
                name=name,
                config=config,
                connection_str=connection_str,
                last_modified_by=user,
                message=message,
                last_modified=timestamp,
                session_factory=self._session_factory,
                event_bus=self.event_bus,
            )
        return self.cache[entity_id]


class SqlEntryUowV1Creator(SqlEntryUowCreator[SqlEntryUnitOfWorkV1]):
    repository_type: str = "sql_entries_v1"

    def _create_uow(self, **kwargs) -> SqlEntryUnitOfWorkV1:
        return SqlEntryUnitOfWorkV1(**kwargs)


class SqlEntryUowV2Creator(SqlEntryUowCreator[SqlEntryUnitOfWorkV2]):
    repository_type: str = "sql_entries_v2"

    def _create_uow(self, **kwargs) -> SqlEntryUnitOfWorkV2:
        return SqlEntryUnitOfWorkV2(**kwargs)
