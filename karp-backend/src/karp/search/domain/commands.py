import pydantic  # noqa: D100, I001

from karp.utility import time


class Command(pydantic.BaseModel):  # noqa: D101
    timestamp: float = pydantic.Field(default_factory=time.utc_now)


class ReindexResource(Command):  # noqa: D101
    resource_id: str
