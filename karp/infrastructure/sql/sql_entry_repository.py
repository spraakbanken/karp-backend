"""SQL repository for entries."""
from karp.infrastructure.sql import sql_models
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from karp.domain.models.entry import (
    Entry,
    EntryOp,
    EntryRepositorySettings,
    EntryStatus,
    EntryRepository,
    create_entry_repository,
)

from karp.infrastructure.sql import db
from karp.infrastructure.sql.sql_repository import SqlRepository


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

        history_model = get_or_create_entry_history_model(table_name)

        # runtime_table = db.get_table(runtime_table_name)
        # if runtime_table is None:
        #     runtime_table = create_entry_runtime_table(
        #         runtime_table_name, history_model, settings["config"]
        #     )

        # runtime_table.create(bind=db.engine, checkfirst=True)
        runtime_model = get_or_create_entry_runtime_model(
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
        # ins_stmt = db.insert(self.history_model)
        # ins_stmt = ins_stmt.values(self._entry_to_history_row(entry))
        # result = self._session.execute(ins_stmt)
        # history_id = result.lastrowid or result.returned_defaults["history_id"]

        ins_stmt = db.insert(self.runtime_model)
        ins_stmt = ins_stmt.values(**self._entry_to_runtime_dict(history_id, entry))
        # ins_stmt = ins_stmt.values(self._entry_to_runtime_row(history_id, entry))
        result = self._session.execute(ins_stmt)
        # self._session.add(
        #     self._entry_to_row(entry)
        #     # self.mapped_class(
        #     #     entry.entry_id,
        #     #     entry.body,
        #     #     entry.id,
        #     #     entry.last_modified,
        #     #     entry.last_modified_by,
        #     #     entry.op,
        #     #     entry.message,
        #     # )
        # )

    def update(self, entry: Entry):
        self._check_has_session()
        history_id = self._insert_history(entry)

        updt_stmt = db.update(self.runtime_model)
        updt_stmt = updt_stmt.where(self.runtime_model.entry_id == entry.entry_id)
        updt_stmt = updt_stmt.values(self._entry_to_runtime_row(history_id, entry))

        result = self._session.execute(updt_stmt)

    def _insert_history(self, entry: Entry):
        self._check_has_session()
        ins_stmt = db.insert(self.history_model)
        ins_stmt = ins_stmt.values(self._entry_to_history_row(entry))
        result = self._session.execute(ins_stmt)
        history_id = result.lastrowid or result.returned_defaults["history_id"]
        return history_id

    def entry_ids(self) -> List[str]:
        self._check_has_session()
        query = self._session.query(self.runtime_model)
        return [row.entry_id for row in query.all()]
        # return [row.entry_id for row in query.filter_by(discarded=False).all()]

    def by_entry_id(self, entry_id: str) -> Optional[Entry]:
        self._check_has_session()
        query = self._session.query(self.history_model)
        # query = query.join(
        #     self.runtime_table,
        #     self.history_model.c.history_id == self.runtime_table.c.history_id,
        # )
        return self._history_row_to_entry(
            query.filter_by(entry_id=entry_id)
            .order_by(self.history_model.last_modified.desc())
            .first()
        )
        # .order_by(self.mapped_class._version.desc())

    def by_id(self, id: str) -> Optional[Entry]:
        self._check_has_session()
        query = self._session.query(self.history_model)
        return (
            query.filter_by(id=id)
            .order_by(self.history_model.last_modified.desc())
            .first()
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
            entry.version,
            entry.last_modified,  # last_modified
            entry.last_modified_by,  # last_modified_by
            entry.body,  # body
            entry.status,  # version
            entry.message,  # message
            entry.op,  # op
            entry.discarded,
        )

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

    def _entry_to_runtime_row(
        self, history_id: int, entry: Entry
    ) -> Tuple[str, int, UUID, bool]:
        return (entry.entry_id, history_id, entry.id, entry.discarded)

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
    history_model = get_or_create_entry_history_model(settings.table_name)

    #     mapped_class = db.map_class_to_some_table(
    #         Entry,
    #         history_model,
    #         f"Entry_{table_name}",
    #         properties={
    #             "_id": table.c.id,
    #             "_version": table.c.version,
    #             "_entry_id": table.c.entry_id,
    #             "_last_modified_by": table.c.user_id,
    #             "_last_modified": table.c.timestamp,
    #             "_body": table.c.body,
    #             "_message": table.c.message,
    #             "_op": table.c.op,
    #         },
    #     )
    runtime_table_name = f"runtime_{settings.table_name}"

    runtime_model = get_or_create_entry_runtime_model(
        runtime_table_name, history_model, settings.config
    )
    return SqlEntryRepository(history_model, runtime_model, settings.config)


class_cache = {}


def get_or_create_entry_history_model(resource_id: str) -> sql_models.BaseHistoryEntry:
    table_name = create_history_table_name(resource_id)
    if table_name in class_cache:
        history_model = class_cache[table_name]
        history_model.__table__.create(bind=db.engine, checkfirst=True)
        return history_model

    attributes = {
        "__tablename__": table_name,
        "__table_args__": None
        # "mysql_character_set": "utf8mb4",
    }

    history_model = type(table_name, (db.Base, sql_models.BaseHistoryEntry), attributes)
    history_model.__table__.create(bind=db.engine, checkfirst=True)
    class_cache[table_name] = history_model
    # table = db.Table(
    #     table_name,
    #     db.metadata,
    #     db.Column("history_id", db.Integer, primary_key=True),
    #     db.Column("id", db.UUIDType, nullable=False),
    #     db.Column("entry_id", db.String(100), nullable=False),
    #     db.Column("last_modified", db.Float, nullable=False),
    #     db.Column("last_modified_by", db.Text, nullable=False),
    #     db.Column("body", db.NestedMutableJson, nullable=False),
    #     db.Column("status", db.Enum(EntryStatus), nullable=False),
    #     db.Column("message", db.Text),
    #     db.Column("op", db.Enum(EntryOp), nullable=False),
    #     db.Column("discarded", db.Boolean, default=False),
    #     db.UniqueConstraint(
    #         "id", "last_modified", name="id_last_modified_unique_constraint"
    #     ),
    #     mysql_character_set="utf8mb4",
    # )

    # db.mapper(
    #     Entry if not _use_aliased else db.aliased(Entry),
    #     table,
    #     properties={
    #         "_id": table.c.id,
    #         "_version": table.c.version,
    #         "_entry_id": table.c.entry_id,
    #         "_last_modified_by": table.c.user_id,
    #         "_last_modified": table.c.timestamp,
    #         "_body": table.c.body,
    #         "_message": table.c.message,
    #         "_op": table.c.op,
    #     },
    #     # non_primary=_non_primary,
    # )
    # if not _use_aliased:
    #     _use_aliased = True
    # table.create(db.engine, checkfirst=True)
    return history_model


def create_runtime_table_name(resource_id: str) -> str:
    return f"runtime_{resource_id}"


def create_history_table_name(resource_id: str) -> str:
    return resource_id


def get_or_create_entry_runtime_model(
    resource_id: str, history_model: db.Table, config: Dict
) -> sql_models.BaseRuntimeEntry:
    table_name = create_runtime_table_name(resource_id)

    if table_name in class_cache:
        runtime_model = class_cache[table_name]
        runtime_model.__table__.create(bind=db.engine, checkfirst=True)
        for child_model in runtime_model.child_tables.values():
            child_model.__table__.create(bind=db.engine, checkfirst=True)
        return runtime_model

    # history_table_name = create_history_table_name(resource_id)

    foreign_key_constraint = db.ForeignKeyConstraint(
        ("history_id",), (history_model.history_id,)
    )

    attributes = {
        "__tablename__": table_name,
        "__table_args__": (foreign_key_constraint,),
    }
    child_tables = {}

    for field_name in config.get("referenceable", ()):
        field = config["fields"][field_name]

        if not field.get("collection"):
            if field["type"] == "integer":
                column_type = db.Integer()
            elif field["type"] == "number":
                column_type = db.Float()
            elif field["type"] == "string":
                column_type = db.String(128)
            else:
                raise NotImplementedError()
            attributes[field_name] = db.Column(column_type)
        else:
            child_table_name = f"{table_name}_{field_name}"
            attributes[field_name] = db.relationship(
                child_table_name,
                backref=table_name,
                cascade="save-update,merge,delete,delete-orphan",
            )
            child_attributes = {
                "__tablename__": child_table_name,
                "__table_args__": (db.PrimaryKeyConstraint("entry_id", field_name),),
                "entry_id": db.Column(
                    db.String(100), db.ForeignKey(f"{table_name}.entry_id")
                ),
            }
            if field["type"] == "object":
                raise ValueError("not possible to reference lists of objects")
            if field["type"] == "integer":
                child_db_column_type = db.Integer()
            elif field["type"] == "number":
                child_db_column_type = db.Float()
            elif field["type"] == "string":
                child_db_column_type = db.String(100)
            else:
                raise NotImplementedError()
            child_attributes[field_name] = db.Column(child_db_column_type)
            child_class = type(child_table_name, (db.Base,), child_attributes)
            child_tables[field_name] = child_class

    runtime_model = type(
        table_name,
        (db.Base, sql_models.BaseRuntimeEntry),
        attributes,
    )
    runtime_model.__table__.create(bind=db.engine, checkfirst=True)
    runtime_model.child_tables = child_tables

    for child_model in runtime_model.child_tables.values():
        child_model.__table__.create(bind=db.engine, checkfirst=True)
    class_cache[table_name] = runtime_model

    return runtime_model
    # print(f"attriubtes = {attributes}")
    # table = db.Table(
    #     table_name,
    #     db.metadata,
    #     # db.Column("entry_id", db.String(100), primary_key=True),
    #     # db.Column("history_id", db.Integer, db.ForeignKey(history_model.c.history_id)),
    #     # # db.Column(
    #     # #     "history_id",
    #     # #     db.Integer,
    #     # #     db.ForeignKey(f"{history_model.name}.history_id"),
    #     # # ),
    #     # db.Column("id", db.UUIDType, nullable=False),
    #     # db.Column("discarded", db.Boolean, nullable=False),
    #     *attributes,
    # )
    # # table.create(db.engine, checkfirst=True)
    # return table
