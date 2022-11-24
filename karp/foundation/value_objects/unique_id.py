"""Handle of unique ids.

Borrowed from https://bitbucket.org/sixty-north/d5-kanban-python
"""
import uuid
import ulid
import typing


UniqueId = uuid.UUID
UniqueIdType = uuid.UUID
typing_UniqueId = uuid.UUID


def make_unique_id(timstamp: typing.Optional[float] = None) -> uuid.UUID:
    """Make a new UniqueId."""
    if timstamp is None:
        return ulid.new().uuid
    else:
        return ulid.from_timestamp(timstamp).uuid
