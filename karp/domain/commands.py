from uuid import UUID
from typing import Dict, Iterable, Optional
import uuid

from pydantic import BaseModel, Field

from karp.utility import time, unique_id

# pylint: disable=unsubscriptable-object


class Command(BaseModel):
    timestamp: float = Field(default_factory=time.utc_now)


# Resource commands


class CreateResource(Command):
    id: UUID
    resource_id: str
    name: str
    config: Dict
    message: str
    created_by: str
    entry_repository_type: Optional[str] = None


class UpdateResource(Command):
    resource_id: str
    version: int
    name: str
    config: Dict
    message: str
    user: str


class PublishResource(Command):
    resource_id: str
    message: str
    user: str


# Entry commands
class AddEntry(Command):
    resource_id: str
    id: unique_id.UniqueId
    entry_id: str
    entry: Dict
    user: str
    message: str


class AddEntries(Command):
    resource_id: str
    ids: Iterable[unique_id.UniqueId]
    entries: Iterable[Dict]
    user: str
    message: str


class UpdateEntry(Command):
    resource_id: str
    entry_id: str
    version: int
    entry: Dict
    user: str
    message: str
    resource_version: Optional[int] = None
    force: bool = False
