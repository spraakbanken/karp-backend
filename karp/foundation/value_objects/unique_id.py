"""Handle of unique ids.

Borrowed from https://bitbucket.org/sixty-north/d5-kanban-python
"""
import uuid
import ulid
import typing


UniqueId = uuid.UUID
UniqueIdType = uuid.UUID
typing_UniqueId = uuid.UUID


def make_unique_id(timestamp: typing.Optional[float] = None) -> UniqueId:
    """Make a new UniqueId."""
    return ulid.new().uuid if timestamp is None else ulid.from_timestamp(timestamp).uuid


def to_unique_id(phrase: typing.Any) -> UniqueId:
    if isinstance(phrase, str):
        return ulid.from_str(phrase).uuid
    raise ValueError()
