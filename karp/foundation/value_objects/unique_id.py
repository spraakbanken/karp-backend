"""Handle of unique ids."""
import typing

import ulid
import ulid.codec

# UniqueId = ulid.ULID

UniqueIdPrimitive = ulid.api.api.ULIDPrimitive
# UniqueIdPrimitive = typing.Union[ulid.api.api.ULIDPrimitive, UniqueIdStr]


class UniqueId(ulid.ULID):
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(examples=["01BJQMF54D093DXEAWZ6JYRPAQ"])

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v) -> "UniqueId":
        if isinstance(v, UniqueId):
            return v  # type: ignore
        if isinstance(v, ulid.ULID):
            return v  # type: ignore
        if not isinstance(v, UniqueIdPrimitive):  # type: ignore
            msg = f"Unsupported type ('{type(v)}')"
            raise TypeError(msg)
        try:
            return ulid.parse(v)  # type: ignore
        except ValueError as err:
            msg = "not a valid ULID"
            raise ValueError(msg) from err

    def __repr__(self) -> str:
        return f"UniqueId({super().__repr__()})"


UniqueIdType = (ulid.ULID, UniqueId)


def make_unique_id(
    t: typing.Optional[ulid.codec.TimestampPrimitive] = None,
) -> UniqueId:
    """Generate an UniqueId that are sortable.

    >>> from karp.foundation.value_objects import make_unique_id
    >>> from datetime import datetime
    >>> old_id = make_unique_id(datetime(1999,12,31,23,59,59))
    >>> make_unique_id() > old_id
    True
    """
    return ulid.new() if t is None else ulid.from_timestamp(t)  # type: ignore


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
        if isinstance(v, (UniqueId, ulid.ULID)):
            return str(v)
        elif not isinstance(v, str):
            raise TypeError("string or UniqueId required")

        if len(v) != 26:
            raise ValueError("invalid uniqueid format")

        return cls(v)

    def __repr__(self) -> str:
        return f"UniqueIdStr({super().__repr__()})"
