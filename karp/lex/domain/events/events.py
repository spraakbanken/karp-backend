import uuid
from typing import Dict

from pydantic import BaseModel

from karp.foundation import events, time
from karp.foundation.value_objects import unique_id


class Event(events.Event, BaseModel):
    timestamp: float

    class Config:
        arbitrary_types_allowed = True


class AppStarted(Event):
    def __init__(self):
        self.timestamp = time.utc_now()


class ResourceCreated(Event):
    entity_id: unique_id.UniqueId
    resource_id: str
    entry_repo_id: unique_id.UniqueId
    name: str
    config: Dict
    user: str
    message: str


class ResourceLoaded(Event):
    entity_id: unique_id.UniqueId
    resource_id: str
    name: str
    config: Dict
    user: str
    message: str
    version: int


class ResourceDiscarded(Event):
    entity_id: unique_id.UniqueId
    resource_id: str
    name: str
    config: Dict
    user: str
    message: str
    version: int


class ResourcePublished(Event):
    entity_id: unique_id.UniqueId
    resource_id: str
    entry_repo_id: unique_id.UniqueId
    version: int
    name: str
    config: Dict
    user: str
    message: str


class ResourceUpdated(Event):
    entity_id: unique_id.UniqueId
    resource_id: str
    entry_repo_id: unique_id.UniqueId
    version: int
    name: str
    config: Dict
    user: str
    message: str


class EntryAdded(Event):
    entity_id: unique_id.UniqueId
    repo_id: unique_id.UniqueId
    # entry_id: str
    body: Dict
    message: str
    user: str


class EntryUpdated(Event):
    entity_id: unique_id.UniqueId
    repo_id: unique_id.UniqueId
    # entry_id: str
    body: Dict
    message: str
    user: str
    version: int


class EntryDeleted(Event):
    entity_id: unique_id.UniqueId
    repo_id: unique_id.UniqueId
    # entry_id: str
    version: int
    message: str
    user: str
