from uuid import UUID
from typing import Dict

from pydantic import BaseModel


class Command:
    pass


class CreateResource(BaseModel, Command):
    id: UUID
    resource_id: str
    name: str
    config: Dict
    message: str
