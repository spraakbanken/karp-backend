import pydantic

from karp.utility import time


class Command(pydantic.BaseModel):
    timestamp: float = pydantic.Field(default_factory=time.utc_now)


class ReindexResource(Command):
    resource_id: str
