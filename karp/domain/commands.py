from uuid import UUID
from typing import Dict

from pydantic import BaseModel, Field

from karp.utility.time import utc_now


class Command(BaseModel):
    timestamp: float = Field(default_factory=utc_now)


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
