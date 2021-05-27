from uuid import UUID
from typing import Dict

from pydantic import BaseModel


class CreateResourceCommand(BaseModel):
    id: UUID
    resource_id: str
    name: str
    config: Dict
    message: str
