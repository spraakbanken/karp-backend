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


class ResourceCreated(Event):  # noqa: D101
    entity_id: unique_id.UniqueId
    resource_id: str
    entry_repo_id: unique_id.UniqueId
    name: str
    config: Dict
    user: str
    message: str


class ResourceLoaded(Event):  # noqa: D101
    entity_id: unique_id.UniqueId
    resource_id: str
    name: str
    config: Dict
    user: str
    message: str
    version: int


class ResourceDiscarded(Event):  # noqa: D101
    entity_id: unique_id.UniqueId
    resource_id: str
    name: str
    config: Dict
    user: str
    message: str
    version: int


class ResourcePublished(Event):  # noqa: D101
    entity_id: unique_id.UniqueId
    resource_id: str
    entry_repo_id: unique_id.UniqueId
    version: int
    name: str
    config: Dict
    user: str
    message: str


class ResourceUpdated(Event):  # noqa: D101
    entity_id: unique_id.UniqueId
    resource_id: str
    entry_repo_id: unique_id.UniqueId
    version: int
    name: str
    config: Dict
    user: str
    message: str


class EntryAdded(Event):  # noqa: D101
    entity_id: unique_id.UniqueId
    repo_id: unique_id.UniqueId
    # entry_id: str
    body: Dict
    message: str
    user: str


class EntryUpdated(Event):  # noqa: D101
    entity_id: unique_id.UniqueId
    repo_id: unique_id.UniqueId
    # entry_id: str
    body: Dict
    message: str
    user: str
    version: int


class EntryDeleted(Event):  # noqa: D101
    entity_id: unique_id.UniqueId
    repo_id: unique_id.UniqueId
    # entry_id: str
    version: int
    message: str
    user: str
