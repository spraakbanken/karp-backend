from uuid import UUID
from typing import Dict, Optional
import uuid

from pydantic import BaseModel, Field

from karp.utility.time import utc_now

# pylint: disable=unsubscriptable-object


class Command(BaseModel):
    timestamp: float = Field(default_factory=utc_now)


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


# Entry commands
class AddEntry(Command):
    resource_id: str
    id: uuid.UUID
    entry_id: str
    body: Dict
    user: str
    message: str


class UpdateEntry(Command):
    resource_id: str
    entry_id: str
    body: Dict
    user: str
    message: str
