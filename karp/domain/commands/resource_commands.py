from uuid import UUID
from typing import Dict

from pydantic import BaseModel


class CreateResourceCommand(BaseModel):
    resource_id: UUID
    name: str
    short_name: str
    config: Dict
    message: str
