from typing import Dict  # noqa: D100

from karp.foundation import events, time
from karp.foundation.value_objects import unique_id
from pydantic import BaseModel


class Event(events.Event, BaseModel):  # noqa: D101
    timestamp: float

    class Config:  # noqa: D106
        arbitrary_types_allowed = True


class AppStarted(Event):  # noqa: D101
    def __init__(self):  # noqa: D107, ANN204
        self.timestamp = time.utc_now()


class ResourceCreated(Event):
    """Event emitted when a resource is created."""
    
    entity_id: unique_id.UniqueIdStr
    resource_id: str
    entry_repo_id: unique_id.UniqueIdStr
    name: str
    config: dict
    user: str
    message: str


# class ResourceLoaded(Event):
#     entity_id: unique_id.UniqueIdStr
#     resource_id: str
#     name: str
#     config: dict
#     user: str
#     message: str
#     version: int


class ResourceDiscarded(Event):  # noqa: D101
    entity_id: unique_id.UniqueIdStr
    resource_id: str
    name: str
    config: dict
    user: str
    message: str
    version: int


class ResourcePublished(Event):  # noqa: D101
    entity_id: unique_id.UniqueIdStr
    resource_id: str
    entry_repo_id: unique_id.UniqueIdStr
    version: int
    name: str
    config: Dict
    user: str
    message: str


class ResourceUpdated(Event):  # noqa: D101
    entity_id: unique_id.UniqueIdStr
    resource_id: str
    entry_repo_id: unique_id.UniqueIdStr
    version: int
    name: str
    config: dict
    user: str
    message: str


class EntryAdded(Event):  # noqa: D101
    entity_id: unique_id.UniqueIdStr
    repo_id: unique_id.UniqueIdStr
    body: dict
    message: str
    user: str


class EntryUpdated(Event):  # noqa: D101
    entity_id: unique_id.UniqueIdStr
    repo_id: unique_id.UniqueIdStr
    body: dict
    message: str
    user: str
    version: int


class EntryDeleted(Event):  # noqa: D101
    entity_id: unique_id.UniqueIdStr
    repo_id: unique_id.UniqueIdStr
    version: int
    message: str
    user: str
