from dataclasses import dataclass
import uuid


class Event:
    pass


@dataclass
class ResourceCreated(Event):
    id: uuid.UUID
