"""Handle of unique ids."""

import typing

import ulid
import ulid.codec
from pydantic_core import core_schema


class UniqueId(ulid.ULID):
    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        json_schema = handler(core_schema.str_schema())
        json_schema["examples"] = ["01BJQMF54D093DXEAWZ6JYRPAQ"]
        return json_schema

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.any_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def validate(cls, v) -> "UniqueId":
        if isinstance(v, UniqueId):
            return v  # type: ignore
        if isinstance(v, ulid.ULID):
            return v  # type: ignore
        if not isinstance(v, (str, bytes, bytearray, memoryview)):  # type: ignore
            msg = f"Unsupported type ('{type(v)}')"
            raise TypeError(msg)
        try:
            return ulid.parse(v)  # type: ignore
        except ValueError as err:
            msg = "not a valid ULID"
            raise ValueError(msg) from err

    def __repr__(self) -> str:
        return f"UniqueId({super().__repr__()})"


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
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        json_schema = handler(core_schema)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema["examples"] = ["01BJQMF54D093DXEAWZ6JYRPAQ"]
        return json_schema

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.any_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )

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
