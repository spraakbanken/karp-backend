"""SQL repositories for entries."""
import inspect
import logging
import typing
from typing import Dict, List, Optional, Tuple
from uuid import UUID

import injector
import regex
import sqlalchemy as sa
from sqlalchemy import sql
from sqlalchemy.orm import sessionmaker
import logging

from karp.foundation.value_objects import UniqueId
from karp.foundation.events import EventBus
from karp.lex.domain import errors
from karp.lex.application import repositories
# from karp.domain.errors import NonExistingField, RepositoryError
from karp.lex.domain.entities.entry import (  # EntryRepositorySettings,; EntryRepository,; create_entry_repository,
    Entry, EntryOp, EntryStatus)
from karp.db_infrastructure import db
from karp.lex_infrastructure.sql import sql_models
from karp.db_infrastructure.sql_repository import SqlRepository
from karp.db_infrastructure.sql_unit_of_work import SqlUnitOfWork

logger = logging.getLogger(__name__)

DUPLICATE_PATTERN = r"Duplicate entry '(.+)' for key '(\w+)'"
DUPLICATE_PROG = regex.compile(DUPLICATE_PATTERN)
NO_PROPERTY_PATTERN = regex.compile(r"has no property '(\w+)'")


class SqlEntryRepository(
    repositories.EntryRepository, SqlRepository
):
    def __init__(
        self,
        history_model,
        runtime_model,
        resource_config: Dict,
        # resource_id: str,
        # mapped_class: Any
        *,
        session: db.Session,
    ):
        if not session:
            raise TypeError("session can't be None")
        repositories.EntryRepository.__init__(self)
        SqlRepository.__init__(self, session=session)
        self.history_model = history_model
        self.runtime_model = runtime_model
        self.resource_config = resource_config
        # self.mapped_class = mapped_class
        # self.resource_id = resource_id

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
        try:
            table_name = name
        except KeyError:
            raise ValueError("Missing 'table_name' in settings.")

        # history_model = db.get_table(table_name)
        # if history_model is None:
        #     history_model = create_history_entry_table(table_name)
        # history_model.create(bind=db.engine, checkfirst=True)

        logger.warning({'table_name': table_name})
        history_model = sql_models.get_or_create_entry_history_model(
            table_name)

        # runtime_table = db.get_table(runtime_table_name)
        # if runtime_table is None:
        #     runtime_table = create_entry_runtime_table(
        #         runtime_table_name, history_model, settings["config"]
        #     )

        if session:
            history_model.__table__.create(bind=session.bind, checkfirst=True)
        # runtime_table.create(bind=db.engine, checkfirst=True)
        runtime_model = sql_models.get_or_create_entry_runtime_model(
            table_name, history_model, resource_config
        )
        if session:
            runtime_model.__table__.create(bind=session.bind, checkfirst=True)
            for child_model in runtime_model.child_tables.values():
                child_model.__table__.create(
                    bind=session.bind, checkfirst=True)
        return cls(
            history_model=history_model,
            runtime_model=runtime_model,
            resource_config=resource_config,
            # resource_id=settings["resource_id"],
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

        history_id = self._insert_history(entry)

        runtime_entry_raw = self._entry_to_runtime_dict(history_id, entry)
        try:
            current_db_entry = (
                self._session.query(self.runtime_model)
                .filter_by(entity_id=entry.entity_id)
                .first()
            )

            if not current_db_entry:
                return self._session.add(
                    self.runtime_model(
                        **runtime_entry_raw
                    )
                )

            for key, value in runtime_entry_raw.items():
                setattr(current_db_entry, key, value)
#            update_result = self._session.query(
#                self.runtime_model
#            ).filter_by(
#                id=entry.id
#            ).update(
#                runtime_entry_raw,
#            )
#
#            if update_result != 1:
#                self._session.add(
#                    self.runtime_model(
#                        **runtime_entry_raw
#                    )
#                )
            # return self._session.add(runtime_entry)
        except db.exc.DBAPIError as exc:
            logger.exception('db error')
            raise errors.RepositoryError("db failure") from exc

    def _update(self, entry: Entry):
        self._check_has_session()
        history_id = self._insert_history(entry)

        current_db_entry = (
            self._session.query(self.runtime_model)
            .filter_by(entry_id=entry.entry_id)
            .first()
        )

        if not current_db_entry:
            raise errors.RepositoryError(f"Could not find {entry.entry_id}")

        runtime_dict = self._entry_to_runtime_dict(history_id, entry)
        for key, value in runtime_dict.items():
            setattr(current_db_entry, key, value)

    @classmethod
    def primary_key(cls):
        return "entry_id"

    def move(self, entry: Entry, *, old_entry_id: str):
        self._check_has_session()

        db_entry = (
            self._session.query(self.runtime_model)
            .filter_by(entry_id=old_entry_id)
            .first()
        )
        if not db_entry:
            raise errors.RepositoryError(f"Could not find {entry.entry_id}")
        db_entry.discarded = True

        return self.save(entry)

    def delete(self, entry: Entry):
        self._check_has_session()

        self._insert_history(entry)

        db_entry = (
            self._session.query(self.runtime_model)
            .filter_by(entry_id=entry.entry_id)
            .first()
        )
        if not db_entry:
            raise errors.RepositoryError(f"Could not find {entry.entry_id}")
        db_entry.discarded = True

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

    def entry_ids(self) -> List[str]:
        self._check_has_session()
        query = self._session.query(
            self.runtime_model).filter_by(discarded=False)
        return [row.entry_id for row in query.all()]
        # return [row.entry_id for row in query.filter_by(discarded=False).all()]

    def _by_entry_id(
        self, entry_id: str, *, version: Optional[int] = None
    ) -> Optional[Entry]:
        self._check_has_session()
        query = self._session.query(self.history_model)
        # query = query.join(
        #     self.runtime_table,
        #     self.history_model.c.history_id == self.runtime_table.c.history_id,
        # )
        query = query.filter_by(entry_id=entry_id)
        if version:
            query = query.filter_by(version=version)
        else:
            query = query.order_by(self.history_model.version.desc())
        row = query.first()
        return self._history_row_to_entry(row) if row else None

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

    def history_by_entry_id(self, entry_id: str) -> List[Entry]:
        self._check_has_session()
        query = self._session.query(self.history_model)
        # query = query.join(
        #     self.runtime_table, self.history_model.c.id == self.runtime_table.c.id
        # )
        return query.filter_by(entry_id=entry_id).all()

    def teardown(self):
        """Use for testing purpose."""
        logger.info("starting teardown")
        #         for child_model in self.runtime_model.child_tables.values():
        #             print(f"droping child_model {child_model} ...")
        #             child_model.__table__.drop(bind=db.engine)
        #         print("droping runtime_model ...")
        #         self.runtime_model.__table__.drop(bind=db.engine)
        logger.info("droping history_model ...")
        self.history_model.__table__.drop(bind=self._session.bind)
        logger.info("dropped history_model")

        # db.metadata.drop_all(
        #     bind=db.engine, tables=[self.runtime_model, self.history_model]
        # )

    def all_entries(self) -> typing.Iterable[Entry]:
        self._check_has_session()

        subq = sql.select(
            self.history_model.entity_id,
            sa.func.max(self.history_model.last_modified).label('maxdate')
        ).group_by(self.history_model.entity_id).subquery('t2')

        stmt = sql.select(self.history_model).join(
            subq,
            sa.and_(
                self.history_model.entity_id == subq.c.entity_id,
                self.history_model.last_modified == subq.c.maxdate,
                self.history_model.discarded == False,
            )
        )
        query = self._session.execute(stmt).scalars()
        # query = self._session.query(
        #     self.history_model).filter_by(discarded=False)
        return [self._history_row_to_entry(db_entry) for db_entry in query.all()]

    def get_total_entries(self) -> int:
        self._check_has_session()
        query = self._session.query(
            self.runtime_model.discarded).filter_by(discarded=False)
        return query.count()

    def by_referenceable(self, filters: Optional[Dict] = None, **kwargs) -> List[Entry]:
        self._check_has_session()
        # query = self._session.query(self.runtime_model)
        query = self._session.query(self.runtime_model, self.history_model).filter(
            self.runtime_model.history_id == self.history_model.history_id
        )
        if filters is None:
            if kwargs is None:
                raise RuntimeError("")
            else:
                filters = kwargs

        joined_filters = []
        simple_filters = {}

        for filter_key in filters.keys():
            # tmp = collections.defaultdict(dict)
            if filter_key in self.resource_config[
                "referenceable"
            ] and self.resource_config["fields"][filter_key].get("collection"):
                logger.debug('collection field', extra={
                             'filter_key': filter_key})
                # child_cls = self.runtime_model.child_tables[filter_key]
                # tmp[child_cls.__tablename__][filter_key] = filters[filter_key]
                # print(f"tmp.values() = {tmp.values()}")
                joined_filters.append({filter_key: filters[filter_key]})
                # query = query.filter(
                #     getattr(self.runtime_model, filter_key).any(filters[filter_key])
                # )
                # query = self._session.query(self.runtime_model.child_tables[filter_key])
                # return query.all()
            else:
                simple_filters[filter_key] = filters[filter_key]
            # joined_filters.extend(tmp.values())

        try:
            query = query.filter_by(**simple_filters)
        except db.exc.InvalidRequestError as exc:
            match = NO_PROPERTY_PATTERN.search(str(exc))
            if match:
                raise errors.NonExistingField(match.group(1)) from exc
            else:
                raise errors.RepositoryError(
                    "Unknown invalid request") from exc

        for child_filters in joined_filters:
            child_table_name = list(child_filters.keys())[0]
            logger.debug('child table name', extra={
                         'table_name': child_table_name})
            child_cls = self.runtime_model.child_tables[child_table_name]
            child_query = self._session.query(
                child_cls).filter_by(**child_filters)
            for child_e in child_query:
                logger.debug('child hit',  extra={'child_hit': child_e})
            query = query.join(child_cls).filter_by(**child_filters)
        # result = query.filter_by(**kwargs).all()
        # # query = self._session.query(self.history_model)
        # # query = query.join(
        # #     self.runtime_table,
        # #     self.history_model.c.history_id == self.runtime_table.c.history_id,
        # # )
        # # result = query.filter_by(larger_place=7).all()
        # print(f"result = {result}")
        # return result
        # return query.all()
        return [self._history_row_to_entry(db_entry) for _, db_entry in query.all()]

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
            query = query.filter_by(entry_id=entry_id)
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

    # def _entry_to_history_row(
    #     self, entry: Entry
    # ) -> Tuple[None, UUID, str, int, float, str, Dict, EntryStatus, str, EntryOp, bool]:
    #     return (
    #         None,  # history_id
    #         entry.id,  # id
    #         entry.entry_id,  # entry_id
    #         entry.version,  # version
    #         entry.last_modified,  # last_modified
    #         entry.last_modified_by,  # last_modified_by
    #         entry.body,  # body
    #         entry.status,  # version
    #         entry.message,  # message
    #         entry.op,  # op
    #         entry.discarded,
    #     )

    def _entry_to_history_dict(
        self, entry: Entry, history_id: Optional[int] = None
    ) -> Dict:
        return {
            "history_id": history_id,
            "entity_id": entry.entity_id,
            "entry_id": entry.entry_id,
            "version": entry.version,
            "last_modified": entry.last_modified,
            "last_modified_by": entry.last_modified_by,
            "body": entry.body,
            "status": entry.status,
            "message": entry.message,
            "op": entry.op,
            "discarded": entry.discarded,
            'repo_id': entry.repo_id,
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
            entry_id=row.entry_id,
            # resource_id=self.resource_id,
        )

    def _entry_to_runtime_dict(self, history_id: int, entry: Entry) -> Dict:
        _entry = {
            "entry_id": entry.entry_id,
            "history_id": history_id,
            "entity_id": entry.entity_id,
            "discarded": entry.discarded,
        }
        for field_name in self.resource_config.get("referenceable", ()):
            field_val = entry.body.get(field_name)
            if field_val is None:
                continue
            if self.resource_config["fields"][field_name].get("collection"):
                child_table = self.runtime_model.child_tables[field_name]
                for elem in field_val:
                    if field_name not in _entry:
                        _entry[field_name] = []
                    _entry[field_name].append(
                        child_table(**{field_name: elem}))
            else:
                _entry[field_name] = field_val
        return _entry


class SqlEntryUnitOfWork(
    SqlUnitOfWork,
    repositories.EntryUnitOfWork,
):
    repository_type: str = 'sql_entries_v1'

    def __init__(
        self,
        session_factory: sessionmaker,
        event_bus: EventBus,
        **kwargs,

    ):
        SqlUnitOfWork.__init__(self)
        repositories.EntryUnitOfWork.__init__(
            self, event_bus=event_bus, **kwargs)
        self.session_factory = session_factory
        self._entries = None
        self._session = None

    def _begin(self):
        if self._session is None:
            self._session = self.session_factory()
        if self._entries is None:
            self._entries = SqlEntryRepository.from_dict(
                name=self.name,
                resource_config=self.config,
                session=self._session
            )
        return self

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
# ===== Value objects =====
# class SqlEntryRepositorySettings(EntryRepositorySettings):
#     def __init__(self, *, table_name: str, config: Dict):
#         self.table_name = table_name
#         self.config = config


# @create_entry_repository.register(SqlEntryRepositorySettings)
# def _(settings: SqlEntryRepositorySettings) -> SqlEntryRepository:
#     history_model = sql_models.get_or_create_entry_history_model(settings.table_name)

#     runtime_table_name = f"runtime_{settings.table_name}"

#     runtime_model = sql_models.get_or_create_entry_runtime_model(
#         runtime_table_name, history_model, settings.config
#     )
#     return SqlEntryRepository(history_model, runtime_model, settings.config)

class SqlEntryUowCreator:
    repository_type: str = SqlEntryUnitOfWork.repository_type

    @injector.inject
    def __init__(
        self,
        session_factory: sessionmaker,
        event_bus: EventBus,
    ):
        self._session_factory = session_factory
        self.event_bus = event_bus
        self.cache = {}

    def __call__(
        self,
        entity_id: UniqueId,
        name: str,
        config: Dict,
        connection_str: Optional[str],
        user: str,
        message: str,
        timestamp: float,
    ) -> SqlEntryUnitOfWork:
        if entity_id not in self.cache:
            self.cache[entity_id] = SqlEntryUnitOfWork(
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
