from sqlalchemy import (
    JSON,
    Column,
    Enum,
    Integer,
    String,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.schema import (
    UniqueConstraint,
)
from sqlalchemy.types import Boolean, Float, Text
from sqlalchemy_json import NestedMutableJson

from karp.db_infrastructure.types import ULIDType
from karp.lex.domain import entities
from karp.lex.domain.entities.entry import EntryOp, EntryStatus
from karp.lex.domain.entities.resource import ResourceOp

Base = declarative_base()


class ResourceModel(Base):
    __tablename__ = "resources"
    history_id = Column(Integer, primary_key=True)
    entity_id = Column(ULIDType, nullable=False)
    resource_id = Column(String(32), nullable=False)
    resource_type = Column(String(32), nullable=False)
    version = Column(Integer, nullable=False)
    name = Column(String(64), nullable=False)
    table_name = Column(String(64), nullable=False)
    config = Column(NestedMutableJson, nullable=False)
    is_published = Column(Boolean, index=True, nullable=True, default=None)
    last_modified = Column(Float(precision=53), nullable=False)
    last_modified_by = Column(String(100), nullable=False)
    message = Column(String(100), nullable=False)
    op = Column(Enum(ResourceOp), nullable=False)
    discarded = Column(Boolean, default=False)
    __table_args__ = (
        UniqueConstraint("entity_id", "version", name="entity_id_version_unique_constraint"),
        UniqueConstraint("table_name", "version", name="table_name_version_unique_constraint"),
        # TODO only one resource can be active, but several can be inactive
        #    here is how to do it in MariaDB, unclear whether this is possible using SQLAlchemy
        #    `virtual_column` char(0) as (if(active,'', NULL)) persistent
        #    and
        #    UNIQUE KEY `resource_version_unique_active` (`resource_id`,`virtual_column`)
        #    this works because the tuple (saldo, NULL) is not equal to (saldo, NULL)
    )

    def __repr__(self):
        return """<ResourceModel(
                    history_id={},
                    entity_id={},
                    resource_id={},
                    version={},
                    name={},
                    config={},
                    table_name={},
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
            self.table_name,
            self.is_published,
            self.last_modified,
            self.last_modified_by,
            self.discarded,
        )

    def to_entity(self) -> entities.Resource:
        return entities.Resource(
            id=self.entity_id,
            resource_id=self.resource_id,
            version=self.version,
            name=self.name,
            config=self.config,
            table_name=self.table_name,
            is_published=self.is_published,
            last_modified=self.last_modified,
            last_modified_by=self.last_modified_by,
            discarded=self.discarded,
            message=self.message,
        )

    @staticmethod
    def from_entity(resource: entities.Resource) -> "ResourceModel":
        return ResourceModel(
            history_id=None,
            entity_id=resource.entity_id,
            resource_id=resource.resource_id,
            resource_type=resource.resource_type,
            version=resource.version,
            name=resource.name,
            config=resource.config,
            table_name=resource.table_name,
            is_published=resource.is_published,
            last_modified=resource.last_modified,
            last_modified_by=resource.last_modified_by,
            message=resource.message,
            op=resource.op,
            discarded=resource.discarded,
        )


class BaseHistoryEntry:
    history_id = Column(Integer, primary_key=True)
    entity_id = Column(ULIDType, nullable=False)
    version = Column(Integer, nullable=False)
    last_modified = Column(Float(53), nullable=False)
    last_modified_by = Column(String(100), nullable=False)
    body = Column(JSON, nullable=False)
    status = Column(Enum(EntryStatus), nullable=False)
    message = Column(Text(length=120))
    op = Column(Enum(EntryOp), nullable=False)
    discarded = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("entity_id", "version", name="id_version_unique_constraint"),
    )

    @classmethod
    def from_entity(cls, entry: entities.Entry):
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
        )


# Dynamic models


def get_or_create_entry_history_model(
    resource_id: str,
) -> BaseHistoryEntry:
    if resource_id in class_cache:
        history_model = class_cache[resource_id]
        return history_model

    attributes = {
        "__tablename__": resource_id,
    }

    sqlalchemy_class = type(resource_id, (Base, BaseHistoryEntry), attributes)
    class_cache[resource_id] = sqlalchemy_class
    return sqlalchemy_class


class_cache = {}
