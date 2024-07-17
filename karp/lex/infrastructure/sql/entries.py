import logging
import typing
from typing import Dict, List, Optional

import sqlalchemy as sa
from sqlalchemy import Engine, sql
from sqlalchemy.orm.session import Session

from karp.foundation.repository import Repository
from karp.foundation.value_objects import UniqueId
from karp.lex.domain import errors
from karp.lex.domain.entities import Resource
from karp.lex.domain.entities.entry import Entry

from . import models

logger = logging.getLogger(__name__)


class EntryRepository(Repository):
    def __init__(self, session: Session, resource: Resource):
        self._session = session
        self._name = resource.resource_id
        self._config = resource.config
        self.resource = resource
        self.history_model = models.get_or_create_entry_history_model(resource.table_name)

    @property
    def name(self) -> str:
        return self._name

    @property
    def config(self) -> Dict:
        return self._config

    @property
    def _engine(self):
        result = self._session.get_bind()
        assert isinstance(result, Engine)  # noqa: S101
        return result

    def create_table(self):
        # We bind to self._engine instead of self._session because CREATE TABLE
        # automatically commits the transaction, which we don't want
        # (using self._engine makes it run in its own transaction)
        self.history_model.__table__.create(bind=self._engine, checkfirst=True)

    def drop_table(self):
        self.history_model.__table__.drop(bind=self._engine, checkfirst=True)

    def _save(self, entry: Entry):
        entry_dto = self.history_model.from_entity(entry)
        self._session.add(entry_dto)

    def entity_ids(self) -> List[str]:
        stmt = self._stmt_latest_not_discarded()
        stmt = stmt.order_by(self.history_model.last_modified.desc())
        query = self._session.execute(stmt).scalars()
        # query = self._session.query(self.history_model).filter_by(discarded=False)
        return [row.entity_id for row in query.all()]

    def by_id(
        self,
        id_: UniqueId,
        *,
        version: Optional[int] = None,
        after_date: Optional[float] = None,
        before_date: Optional[float] = None,
        oldest_first: bool = False,
        **kwargs,
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

    def all_entries(self) -> typing.Iterable[Entry]:
        stmt = self._stmt_latest_not_discarded()
        query = self._session.execute(stmt).scalars()

        return (self._history_row_to_entry(db_entry) for db_entry in query)

    # TODO Rename this here and in `entity_ids` and `all_entries`
    def _stmt_latest_not_discarded(self):
        subq = self._subq_for_latest()
        return sql.select(self.history_model).join(
            subq,
            sa.and_(
                self.history_model.entity_id == subq.c.entity_id,
                self.history_model.history_id == subq.c.history_id,
                self.history_model.discarded == False,  # noqa: E712
            ),
        )

    def _subq_for_latest(self) -> sql.Subquery:
        return (
            sql.select(
                self.history_model.entity_id,
                sa.func.max(self.history_model.history_id).label("history_id"),
            )
            .group_by(self.history_model.entity_id)
            .subquery("t2")
        )

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
            resource_id=self.resource.resource_id,
        )
