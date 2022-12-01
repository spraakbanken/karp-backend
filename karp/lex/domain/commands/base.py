import pydantic

from karp.foundation import commands
from karp.utility import time


class Command(pydantic.BaseModel, commands.Command):
    timestamp: float = pydantic.Field(default_factory=time.utc_now)

    class Config:
        arbitrary_types_allowed = True
