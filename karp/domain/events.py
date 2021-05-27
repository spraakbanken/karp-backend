from dataclasses import dataclass
from typing import Dict
import uuid


class Event:
    pass


@dataclass
class ResourceCreated(Event):
    id: uuid.UUID
    resource_id: str
    name: str
    config: Dict
