"""Handle of unique ids.

Borrowed from https://bitbucket.org/sixty-north/d5-kanban-python
"""
import uuid
import typing

import pydantic
import ulid

# UniqueId = uuid.UUID
# UniqueIdType = uuid.UUID
# typing_UniqueId = uuid.UUID
UniqueId = ulid.ULID
UniqueIdType = ulid.ULID
typing_UniqueId = ulid.ULID


def make_unique_id(timestamp: typing.Optional[float] = None) -> UniqueId:
    """Make a new UniqueId."""
    return ulid.new() if timestamp is None else ulid.from_timestamp(timestamp)


def to_unique_id(phrase: typing.Any) -> UniqueId:
    if isinstance(phrase, str):
        return ulid.from_str(phrase)
    raise ValueError()


parse = ulid.parse


class UniqueIdStr(str):
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(examples=["01BJQMF54D093DXEAWZ6JYRPAQ"])

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, UniqueId):
            return str(v)
        elif not isinstance(v, str):
            raise TypeError("string or UniqueId required")

        if len(v) != 26:
            raise ValueError("invalid uniqueid format")

        return cls(v)

    def __repr__(self) -> str:
        return f"UniqueIdStr({super().__repr__()})"


UniqueIdPrimitive = typing.Union[ulid.api.api.ULIDPrimitive, UniqueIdStr]


# def parse(value: UniqueIdPrimitive) -> UniqueId:
#     if isinstance(value, Uni)
