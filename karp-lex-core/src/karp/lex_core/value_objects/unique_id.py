"""Handle of unique ids."""
import typing

import ulid
import ulid.codec

# UniqueId = ulid.ULID

UniqueIdPrimitive = ulid.api.api.ULIDPrimitive
# UniqueIdPrimitive = typing.Union[ulid.api.api.ULIDPrimitive, UniqueIdStr]


class UniqueId(ulid.ULID):  # noqa: D101
    @classmethod
    def __modify_schema__(cls, field_schema):  # noqa: ANN206, ANN001, D105
        field_schema.update(examples=["01BJQMF54D093DXEAWZ6JYRPAQ"])

    @classmethod
    def __get_validators__(cls):  # noqa: ANN206, D105
        yield cls.validate

    @classmethod
    def validate(cls, v) -> "UniqueId":  # noqa: D102, ANN001
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

    def __repr__(self) -> str:  # noqa: D105
        return f"UniqueId({super().__repr__()})"


UniqueIdType = (ulid.ULID, UniqueId)


def make_unique_id(
    t: typing.Optional[ulid.codec.TimestampPrimitive] = None,
) -> UniqueId:
    """Generate an UniqueId that are sortable.

    >>> from karp.lex_core.value_objects import make_unique_id
    >>> from datetime import datetime
    >>> old_id = make_unique_id(datetime(1999,12,31,23,59,59))
    >>> make_unique_id() > old_id
    True
    """
    return ulid.new() if t is None else ulid.from_timestamp(t)  # type: ignore


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
        if isinstance(v, (UniqueId, ulid.ULID)):
            return str(v)
        elif not isinstance(v, str):
            raise TypeError("string or UniqueId required")

        if len(v) != 26:
            raise ValueError("invalid uniqueid format")

        return cls(v)

    def __repr__(self) -> str:  # noqa: D105
        return f"UniqueIdStr({super().__repr__()})"
