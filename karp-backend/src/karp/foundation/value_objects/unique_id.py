"""Handle of unique ids.

Borrowed from https://bitbucket.org/sixty-north/d5-kanban-python
"""
import typing

import pydantic  # noqa: F401
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


def to_unique_id(phrase: typing.Any) -> UniqueId:  # noqa: ANN401, D103
    if isinstance(phrase, str):
        return ulid.from_str(phrase)
    raise ValueError()


parse = ulid.parse


class UniqueIdStr(str):  # noqa: D101
    @classmethod
    def __modify_schema__(cls, field_schema):  # noqa: ANN206, ANN001, D105
        field_schema.update(examples=["01BJQMF54D093DXEAWZ6JYRPAQ"])

    @classmethod
    def __get_validators__(cls):  # noqa: ANN206, D105
        yield cls.validate

    @classmethod
    def validate(cls, v):  # noqa: ANN206, D102, ANN001
        if isinstance(v, UniqueId):
            return str(v)
        elif not isinstance(v, str):
            raise TypeError("string or UniqueId required")

        if len(v) != 26:
            raise ValueError("invalid uniqueid format")

        return cls(v)

    def __repr__(self) -> str:  # noqa: D105
        return f"UniqueIdStr({super().__repr__()})"


UniqueIdPrimitive = typing.Union[ulid.api.api.ULIDPrimitive, UniqueIdStr]


# def parse(value: UniqueIdPrimitive) -> UniqueId:
#     if isinstance(value, Uni)
