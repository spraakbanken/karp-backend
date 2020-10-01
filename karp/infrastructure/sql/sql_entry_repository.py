"""SQL repository for entries."""
import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import regex

from karp.domain.models.entry import (
    Entry,
    EntryOp,
    EntryRepositorySettings,
    EntryStatus,
    EntryRepository,
    create_entry_repository,
)

from karp.infrastructure.sql import db
from karp.infrastructure.sql import sql_models
from karp.infrastructure.sql.sql_repository import SqlRepository

from karp import errors


logger = logging.getLogger("karp")

DUPLICATE_PATTERN = r"Duplicate entry '(.+)' for key '(\w+)'"
DUPLICATE_PROG = regex.compile(DUPLICATE_PATTERN)


class SqlEntryRepository(
    EntryRepository, SqlRepository, repository_type="sql_v1", is_default=True
):
    def __init__(
        self,
        history_model: db.Base,
        runtime_model: db.Base,
        resource_config: Dict,
        # mapped_class: Any
    ):
        super().__init__()
        self.history_model = history_model
        self.runtime_model = runtime_model
        self.resource_config = resource_config
        # self.mapped_class = mapped_class

    @classmethod
    def from_dict(cls, settings: Dict):
        try:
            table_name = settings["table_name"]
        except KeyError:
            raise ValueError("Missing 'table_name' in settings.")

        # history_model = db.get_table(table_name)
        # if history_model is None:
        #     history_model = create_history_entry_table(table_name)
        # history_model.create(bind=db.engine, checkfirst=True)

        history_model = sql_models.get_or_create_entry_history_model(table_name)

        # runtime_table = db.get_table(runtime_table_name)
        # if runtime_table is None:
        #     runtime_table = create_entry_runtime_table(
        #         runtime_table_name, history_model, settings["config"]
        #     )

        # runtime_table.create(bind=db.engine, checkfirst=True)
        runtime_model = sql_models.get_or_create_entry_runtime_model(
            table_name, history_model, settings["config"]
        )
        return cls(
            history_model=history_model,
            runtime_model=runtime_model,
            resource_config=settings["config"],
        )

    @classmethod
    def _create_repository_settings(cls, resource_id: str) -> Dict:
        return {"table_name": resource_id}

    def put(self, entry: Entry):
        self._check_has_session()

        history_id = self._insert_history(entry)

        ins_stmt = db.insert(self.runtime_model)
        ins_stmt = ins_stmt.values(**self._entry_to_runtime_dict(history_id, entry))
        try:
            return self._session.execute(ins_stmt)
        except db.exc.IntegrityError as exc:
            logger.exception(exc)
            match = DUPLICATE_PROG.search(str(exc))
            if match:
                value = match.group(1)
                key = match.group(2)
                if key == "PRIMARY":
                    key = "entry_id"
            else:
                value = "UNKNOWN"
                key = "UNKNOWN"
            raise errors.IntegrityError(key, value)

    def update(self, entry: Entry):
        self._check_has_session()
        history_id = self._insert_history(entry)

        updt_stmt = db.update(self.runtime_model)
        updt_stmt = updt_stmt.where(self.runtime_model.entry_id == entry.entry_id)
        updt_stmt = updt_stmt.values(**self._entry_to_runtime_dict(history_id, entry))

        try:
            return self._session.execute(updt_stmt)
        except db.exc.IntegrityError as exc:
            logger.exception(exc)
            match = DUPLICATE_PROG.search(str(exc))
            if match:
                value = match.group(1)
                key = match.group(2)
                if key == "PRIMARY":
                    key = "entry_id"
            else:
                value = "UNKNOWN"
                key = "UNKNOWN"
            raise errors.IntegrityError(key, value)

    def _insert_history(self, entry: Entry):
        self._check_has_session()
        try:
            ins_stmt = db.insert(self.history_model)
            history_row = self._entry_to_history_row(entry)
            ins_stmt = ins_stmt.values(history_row)
            result = self._session.execute(ins_stmt)
            return result.lastrowid or result.returned_defaults["history_id"]
        except db.exc.IntegrityError as exc:
            logger.exception(exc)
            match = DUPLICATE_PROG.search(str(exc))
            if match:
                value = match.group(1)
                key = match.group(2)
            else:
                value = "UNKNOWN"
                key = "UNKNOWN"
            raise errors.IntegrityError(key, value)

    def entry_ids(self) -> List[str]:
        self._check_has_session()
        query = self._session.query(self.runtime_model).filter_by(discarded=False)
        return [row.entry_id for row in query.all()]
        # return [row.entry_id for row in query.filter_by(discarded=False).all()]

    def by_entry_id(self, entry_id: str) -> Optional[Entry]:
        self._check_has_session()
        query = self._session.query(self.history_model)
        # query = query.join(
        #     self.runtime_table,
        #     self.history_model.c.history_id == self.runtime_table.c.history_id,
        # )
        row = (
            query.filter_by(entry_id=entry_id)
            .order_by(self.history_model.version.desc())
            .first()
        )
        return self._history_row_to_entry(row) if row else None

    def by_id(self, id: str) -> Optional[Entry]:
        self._check_has_session()
        query = self._session.query(self.history_model)
        return (
            query.filter_by(id=id).order_by(self.history_model.version.desc()).first()
        )

    def history_by_entry_id(self, entry_id: str) -> List[Entry]:
        self._check_has_session()
        query = self._session.query(self.history_model)
        # query = query.join(
        #     self.runtime_table, self.history_model.c.id == self.runtime_table.c.id
        # )
        return query.filter_by(entry_id=entry_id).all()

    def teardown(self):
        """Use for testing purpose."""
        for child_model in self.runtime_model.child_tables.values():
            child_model.__table__.drop(bind=db.engine)
        self.runtime_model.__table__.drop(bind=db.engine)
        self.history_model.__table__.drop(bind=db.engine)
        # db.metadata.drop_all(
        #     bind=db.engine, tables=[self.runtime_model, self.history_model]
        # )

    def by_referencable(self, **kwargs) -> List[Entry]:
        self._check_has_session()
        query = self._session.query(self.runtime_model)
        result = query.filter_by(**kwargs).all()
        # query = self._session.query(self.history_model)
        # query = query.join(
        #     self.runtime_table,
        #     self.history_model.c.history_id == self.runtime_table.c.history_id,
        # )
        # result = query.filter_by(larger_place=7).all()
        print(f"result = {result}")
        return result

    def _entry_to_history_row(
        self, entry: Entry
    ) -> Tuple[None, UUID, str, int, float, str, Dict, EntryStatus, str, EntryOp, bool]:
        return (
            None,  # history_id
            entry.id,  # id
            entry.entry_id,  # entry_id
            entry.version,  # version
            entry.last_modified,  # last_modified
            entry.last_modified_by,  # last_modified_by
            entry.body,  # body
            entry.status,  # version
            entry.message,  # message
            entry.op,  # op
            entry.discarded,
        )

    def _entry_to_history_dict(
        self, entry: Entry, history_id: Optional[int] = None
    ) -> Dict:
        return {
            "history_id": history_id,
            "id": entry.id,
            "entry_id": entry.entry_id,
            "version": entry.version,
            "last_modified": entry.last_modified,
            "last_modified_by": entry.last_modified_by,
            "body": entry.body,
            "status": entry.status,
            "message": entry.message,
            "op": entry.op,
            "discarded": entry.discarded,
        }

    def _history_row_to_entry(self, row) -> Entry:
        return Entry(
            entry_id=row.entry_id,
            body=row.body,
            message=row.message,
            status=row.status,
            op=row.op,
            entity_id=row.id,
            last_modified=row.last_modified,
            last_modified_by=row.last_modified_by,
            discarded=row.discarded,
            version=row.version,
        )

    def _entry_to_runtime_dict(self, history_id: int, entry: Entry) -> Dict:
        _entry = {
            "entry_id": entry.entry_id,
            "history_id": history_id,
            "id": entry.id,
            "discarded": entry.discarded,
        }
        for field_name in self.resource_config.get("referenceable", ()):
            field_val = entry.body.get(field_name)
            if field_val is None:
                continue
            if self.resource_config["fields"][field_name].get("collection", False):
                pass
            else:
                _entry[field_name] = field_val
        return _entry


# ===== Value objects =====
class SqlEntryRepositorySettings(EntryRepositorySettings):
    def __init__(self, *, table_name: str, config: Dict):
        self.table_name = table_name
        self.config = config


@create_entry_repository.register(SqlEntryRepositorySettings)
def _(settings: SqlEntryRepositorySettings) -> SqlEntryRepository:
    history_model = sql_models.get_or_create_entry_history_model(settings.table_name)

    runtime_table_name = f"runtime_{settings.table_name}"

    runtime_model = sql_models.get_or_create_entry_runtime_model(
        runtime_table_name, history_model, settings.config
    )
    return SqlEntryRepository(history_model, runtime_model, settings.config)
