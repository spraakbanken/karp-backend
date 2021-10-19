import typing

import pydantic

from karp.foundation.value_objects import unique_id
from karp.foundation import commands
from karp.utility import time


class Command(pydantic.BaseModel, commands.Command):
    timestamp: float = pydantic.Field(default_factory=time.utc_now)


class ReindexResource(Command):
    resource_id: str
