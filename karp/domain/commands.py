from uuid import UUID
from typing import Dict

from pydantic import BaseModel, Field

from karp.utility.time import utc_now


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
    entry_id: str
    body: str
    user: str
    message: str
