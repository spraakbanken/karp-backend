from uuid import UUID
from typing import Dict

from pydantic import BaseModel, Field

from karp.utility.time import utc_now


class Command:
    pass


class CreateResource(BaseModel, Command):
    id: UUID
    resource_id: str
    name: str
    config: Dict
    message: str
    created_by: str
    created_at: float = Field(default_factory=utc_now)


class UpdateResource(BaseModel, Command):
    resource_id: str
    name: str
    config: Dict
    message: str
    user: str
    modified_at: float = Field(default_factory=utc_now)
