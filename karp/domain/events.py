from dataclasses import dataclass
from typing import Dict
import uuid

from karp.foundation import events

from karp.utility import time, unique_id


@dataclass
class Event(events.Event):
    timestamp: float


@dataclass
class AppStarted(Event):
    def __init__(self):
        self.timestamp = time.utc_now()


@dataclass
class ResourceCreated(Event):
    id: uuid.UUID
    resource_id: str
    name: str
    config: Dict
    user: str
    message: str


@dataclass
class ResourceLoaded(Event):
    id: uuid.UUID
    resource_id: str
    name: str
    config: Dict
    user: str
    message: str
    version: int


@dataclass
class ResourceDiscarded(Event):
    id: uuid.UUID
    resource_id: str
    name: str
    config: Dict
    user: str
    message: str
    version: int


@dataclass
class ResourcePublished(Event):
    id: uuid.UUID
    resource_id: str
    version: int
    name: str
    config: Dict
    user: str
    message: str


@dataclass
class ResourceUpdated(Event):
    id: uuid.UUID
    resource_id: str
    version: int
    name: str
    config: Dict
    user: str
    message: str


@dataclass
class EntryAdded(Event):
    id: uuid.UUID
    resource_id: str
    entry_id: str
    body: Dict
    message: str
    user: str


@dataclass
class EntryUpdated(Event):
    id: uuid.UUID
    resource_id: str
    entry_id: str
    body: Dict
    message: str
    user: str
    version: int


@dataclass
class EntryDeleted(Event):
    id: uuid.UUID
    resource_id: str
    entry_id: str
    version: int
    message: str
    user: str
