from dataclasses import dataclass
from typing import Dict
import uuid


@dataclass
class Event:
    timestamp: float


@dataclass
class ResourceCreated(Event):
    id: uuid.UUID
    resource_id: str
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
class EntryDiscarded(Event):
    id: uuid.UUID
    resource_id: str
    entry_id: str
    version: int
    message: str
    user: str
