"""UUIDType borrowed from sqlalchemy-utils and simplified"""

from enum import unique
import uuid

from sqlalchemy import types, util
from karp.foundation.value_objects.unique_id import UniqueId, UniqueIdType


class UUIDType(types.TypeDecorator):
    """
    Stores a UUID in the database natively when it can and falls back to
    a BINARY(16).

    ::

        from karp.db_infrastructure.sqlalchemy_types import UUIDType
        from karp.foundation.value_objects.unique_id import make_unique_id

        class User(Base):
            __tablename__ = 'user'

            id = sa.Column(UUIDType(), primary_key=True, default=make_unique_id)
    """
    impl = types.BINARY(16)

    def __init__(self):
        super().__init__()

    def __repr__(self):
        return 'UUIDType()'

    @staticmethod
    def _coerce(value):
        if value and not isinstance(value, UniqueIdType):
            try:
                value = UniqueId(bytes=value)

            except (TypeError, ValueError):
                value = uuid.UUID(bytes=value)

        return value

    def process_literal_param(self, value, dialect):
        return "'{}'".format(value) if value else value

    def process_bind_param(self, value, dialect):
        if value is None:
            return value

        if not isinstance(value, UniqueIdType):
            value = self._coerce(value)

        return value.bytes

    def process_result_value(self, value, dialect):
        if value is None:
            return value

        return UniqueId(bytes=value)
