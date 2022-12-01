"""Handles all sql db connections."""
import collections
import json
from typing import Any, Dict, Optional

import attr
import sqlalchemy
from sqlalchemy import (
    JSON,
    Column,
    Enum,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    Unicode,
    and_,
    event,
    exc,
    func,
    or_,
)
from sqlalchemy.dialects.mysql import DOUBLE
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.orm import aliased, mapper, relationship
from sqlalchemy.orm.session import Session, sessionmaker
from sqlalchemy.schema import (
    ForeignKeyConstraint,
    PrimaryKeyConstraint,
    UniqueConstraint,
)
from sqlalchemy.sql import delete, insert, update
from sqlalchemy.types import VARCHAR, Boolean, Float, Time, TypeDecorator
from sqlalchemy_json import NestedMutableJson
from sqlalchemy_utils import UUIDType
from karp.db_infrastructure.types import ULIDType


__all__ = ["ULIDType"]

# engine = sqlalchemy.create_engine(config.DB_URL, echo=True)

metadata = MetaData()

Base = declarative_base(metadata=metadata)

# SessionLocal = sessionmaker(bind=engine)


@attr.s(auto_attribs=True)
class SQLEngineSessionfactory:
    engine: Engine = attr.ib()
    session_factory: sessionmaker = attr.ib()
    metadata: MetaData = attr.ib()

    @classmethod
    def from_db_uri(cls, db_uri: str):
        engine = sqlalchemy.create_engine(db_uri)
        session_factory = sessionmaker(bind=engine)
        metadata_ = MetaData()
        return cls(engine, session_factory, metadata_)


_db_handlers: Dict[str, SQLEngineSessionfactory] = dict()


def create_session(db_uri: str) -> Session:
    _assure_in_db_handlers(db_uri)
    return _db_handlers[db_uri].session_factory()


def get_engine(db_uri: str) -> Engine:
    _assure_in_db_handlers(db_uri)
    return _db_handlers[db_uri].engine


def _assure_in_db_handlers(db_uri: str):
    if db_uri not in _db_handlers:
        _db_handlers[db_uri] = SQLEngineSessionfactory.from_db_uri(db_uri)


def _metadata(db_uri: str) -> MetaData:
    _assure_in_db_handlers(db_uri)
    return _db_handlers[db_uri].metadata


def get_table(table_name: str) -> Optional[Table]:
    return metadata.tables.get(table_name)


# def map_class_to_some_table(cls, table: Table, entity_name: str, **mapper_kw):
#     """Use the EntityName-pattern to map a cls to several tables.

#     See https://github.com/sqlalchemy/sqlalchemy/wiki/EntityName for more information.

#     Arguments:
#         table {Table} -- the table to map to
#         entity_name {str} -- the name for the new class

#     Keyword arguments:
#     mapper_kw -- any keyword arguments passed to mapper

#     Raises:
#         ValueError: when?

#     Returns:
#         Any -- the new class constructed
#     """
#     newcls = type(entity_name, (cls,), {})
#     mapper(newcls, table, **mapper_kw)
#     return newcls


# _metadata = MetaData()


# class JsonEncodedDict(TypeDecorator):
#     """Represent an immutable dictionary as a json-encoded-string."""

#     impl = VARCHAR

#     def process_bind_param(self, value, dialect):
#         if value is not None:
#             value = json.dumps(value)
#         return value

#     def process_result_value(self, value, dialect):
#         if value is not None:
#             value = json.loads(value)
#         return value


# class MutableDict(Mutable, dict):
#     """Tracking changes for sql."""

#     @classmethod
#     def coerce(cls, key, value):
#         """Convert plain dicts to MutableDict."""
#         if not isinstance(value, MutableDict):
#             if isinstance(value, dict):
#                 return cls(value)

#             # this call will raise ValueError
#             return Mutable.coerce(key, value)
#         else:
#             return value

#     def __setitem__(self, key, value):
#         """Detect dictionary set events and emit changed event."""
#         dict.__setitem__(self, key, value)
#         self.changed()

#     def __delitem__(self, key, value):
#         """Detect dictionary del events and emit changed event."""
#         dict.__delitem__(self, key, value)
#         self.changed()


# MutableDict.associate_with(JsonEncodedDict)


# class FalseEncodedAsNullBoolean(TypeDecorator):
#     impl = Boolean

#     def process_bind_param(self, value, dialect):
#         if value is False:
#             value = None
#         return value

#     def process_result_value(self, value, dialect):
#         if value is None:
#             return False
#         return value


# class MutableBool(Mutable):
#     @classmethod
#     def coerce(cls, key, value):
#         if isinstance(value, MutableBool):
#             return value
#
#         if isinstance(value, bool):
#             return cls(value)
#
#         return Mutable.coerce(key, value)
#
#     def __setattr__(self, name, value):
#         object.__setattr__(self, name, value)
#         self.changed()


# MutableBool.associate_with(FalseEncodedAsNullBoolean)
