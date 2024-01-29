from typing import Dict  # noqa: D100, I001

from sqlalchemy import (
    JSON,
    Column,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.types import Boolean, Float
from sqlalchemy_json import NestedMutableJson

from sqlalchemy.schema import (
    ForeignKeyConstraint,
    PrimaryKeyConstraint,
    UniqueConstraint,
)

from karp.db_infrastructure.types import ULIDType
from karp.lex.domain import entities
from karp.lex.domain.entities.entry import EntryOp, EntryStatus
from karp.lex.domain.entities.resource import ResourceOp
from karp.lex.application.repositories import EntryUnitOfWork
from karp.db_infrastructure import db


class ResourceModel(db.Base):  # noqa: D101
    __tablename__ = "resources"
    history_id = Column(Integer, primary_key=True)
    entity_id = Column(ULIDType, nullable=False)
    resource_id = Column(String(32), nullable=False)
    resource_type = Column(String(32), nullable=False)
    version = Column(Integer, nullable=False)
    name = Column(String(64), nullable=False)
    entry_repo_id = Column(ULIDType, nullable=False)
    config = Column(NestedMutableJson, nullable=False)
    is_published = Column(Boolean, index=True, nullable=True, default=None)
    last_modified = Column(Float(precision=53), nullable=False)
    last_modified_by = Column(String(100), nullable=False)
    message = Column(String(100), nullable=False)
    op = Column(Enum(ResourceOp), nullable=False)
    discarded = Column(Boolean, default=False)
    __table_args__ = (
        UniqueConstraint("entity_id", "version", name="entity_id_version_unique_constraint"),
        # TODO only one resource can be active, but several can be inactive
        #    here is how to do it in MariaDB, unclear whether this is possible using SQLAlchemy
        #    `virtual_column` char(0) as (if(active,'', NULL)) persistent
        #    and
        #    UNIQUE KEY `resource_version_unique_active` (`resource_id`,`virtual_column`)
        #    this works because the tuple (saldo, NULL) is not equal to (saldo, NULL)
    )

    def __repr__(self):  # noqa: ANN204, D105
        return """<ResourceModel(
                    history_id={},
                    entity_id={},
                    resource_id={},
                    version={},
                    name={},
                    config={},
                    entry_repo_id={},
                    is_published={},
                    last_modified={},
                    last_modified_by={},
                    discarded={},
                ) > """.format(
            self.history_id,
            self.entity_id,
            self.resource_id,
            self.version,
            self.name,
            self.config,
            self.entry_repo_id,
            self.is_published,
            self.last_modified,
            self.last_modified_by,
            self.discarded,
        )

    def to_entity(self) -> entities.Resource:  # noqa: D102
        return entities.Resource(
            id=self.entity_id,
            resource_id=self.resource_id,
            version=self.version,
            name=self.name,
            config=self.config,
            entry_repo_id=self.entry_repo_id,
            is_published=self.is_published,
            last_modified=self.last_modified,
            last_modified_by=self.last_modified_by,
            discarded=self.discarded,
            message=self.message,
        )

    @staticmethod
    def from_entity(resource: entities.Resource) -> "ResourceModel":  # noqa: D102
        return ResourceModel(
            history_id=None,
            entity_id=resource.entity_id,
            resource_id=resource.resource_id,
            resource_type=resource.resource_type,
            version=resource.version,
            name=resource.name,
            config=resource.config,
            entry_repo_id=resource.entry_repository_id,
            is_published=resource.is_published,
            last_modified=resource.last_modified,
            last_modified_by=resource.last_modified_by,
            message=resource.message,
            op=resource.op,
            discarded=resource.discarded,
        )


class EntryUowModel(db.Base):  # noqa: D101
    __tablename__ = "entry_repos"
    history_id = Column(Integer, primary_key=True)
    entity_id = Column(ULIDType, nullable=False)
    type = Column(String(64), nullable=False)  # noqa: A003
    connection_str = Column(String(128))
    name = Column(String(64), nullable=False)
    config = Column(NestedMutableJson, nullable=False)
    last_modified = Column(Float(precision=53), nullable=False)
    last_modified_by = Column(String(100), nullable=False)
    message = Column(String(100), nullable=False)
    discarded = Column(Boolean, default=False)

    @staticmethod
    def from_entity(entry_uow: EntryUnitOfWork) -> "EntryUowModel":  # noqa: D102
        return EntryUowModel(
            history_id=None,
            entity_id=entry_uow.entity_id,
            # TODO legacy field, can be removed from database when migrations are figured out
            type="sql_entries_v2",
            connection_str=entry_uow.connection_str,
            name=entry_uow.name,
            config=entry_uow.config,
            last_modified=entry_uow.last_modified,
            last_modified_by=entry_uow.last_modified_by,
            message=entry_uow.message,
            discarded=entry_uow.discarded,
        )


class BaseRuntimeEntry:  # noqa: D101
    entry_id = Column(
        String(100),
        primary_key=True,
    )
    history_id = Column(Integer, nullable=False)
    entity_id = Column(ULIDType, nullable=False)
    discarded = Column(Boolean, nullable=False)


class BaseHistoryEntry:  # noqa: D101
    history_id = Column(Integer, primary_key=True)
    entity_id = Column(ULIDType, nullable=False)
    repo_id = Column(ULIDType, nullable=False)
    version = Column(Integer, nullable=False)
    last_modified = Column(Float(53), nullable=False)
    last_modified_by = Column(String(100), nullable=False)
    body = Column(JSON, nullable=False)
    status = Column(Enum(EntryStatus), nullable=False)
    message = Column(Text(length=120))
    op = Column(Enum(EntryOp), nullable=False)
    discarded = Column(Boolean, default=False)

    @classmethod
    @declared_attr
    def __table_args__(cls):  # noqa: ANN206, D105
        return UniqueConstraint("entity_id", "version", name="id_version_unique_constraint")

    @classmethod
    def from_entity(cls, entry: entities.Entry):  # noqa: ANN206, D102
        return cls(
            history_id=None,
            entity_id=entry.entity_id,
            # entry_id=entry.entry_id,
            version=entry.version,
            last_modified=entry.last_modified,
            last_modified_by=entry.last_modified_by,
            body=entry.body,
            status=entry.status,
            message=entry.message,
            op=entry.op,
            discarded=entry.discarded,
            repo_id=entry.repo_id,
        )


# Dynamic models


def get_or_create_entry_history_model(  # noqa: D103
    resource_id: str,
) -> BaseHistoryEntry:
    history_table_name = create_history_table_name(resource_id)
    if history_table_name in class_cache:
        history_model = class_cache[history_table_name]
        return history_model

    attributes = {
        "__tablename__": history_table_name,
        "__table_args__": None,
    }

    sqlalchemy_class = type(history_table_name, (db.Base, BaseHistoryEntry), attributes)
    class_cache[history_table_name] = sqlalchemy_class
    return sqlalchemy_class


def get_or_create_entry_runtime_model(  # noqa: D103, C901
    resource_id: str, history_model: Table, config: Dict
) -> BaseRuntimeEntry:
    table_name = create_runtime_table_name(resource_id)

    if table_name in class_cache:
        runtime_model = class_cache[table_name]
        return runtime_model

    foreign_key_constraint = ForeignKeyConstraint(
        ["history_id"], [f"{history_model.__tablename__}.history_id"]
    )

    attributes = {
        "__tablename__": table_name,
        "__table_args__": (foreign_key_constraint,),
    }
    child_tables = {}

    sqlalchemy_class = type(
        table_name,
        (db.Base, BaseRuntimeEntry),
        attributes,
    )
    sqlalchemy_class.child_tables = child_tables

    class_cache[table_name] = sqlalchemy_class

    return sqlalchemy_class


class_cache = {}


# Helpers


def create_runtime_table_name(resource_id: str) -> str:  # noqa: D103
    return f"runtime_{resource_id}"


def create_history_table_name(resource_id: str) -> str:  # noqa: D103
    return resource_id
