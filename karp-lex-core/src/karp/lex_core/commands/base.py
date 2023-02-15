"""Base class for lex commands"""

from datetime import datetime, timezone
from typing import Optional

import pydantic
from karp.lex_core import alias_generators


def utc_now() -> float:
    """A UTC timestamp in seconds.

    This function may return the same timestamp twice.
    """
    return datetime.now(timezone.utc).timestamp()


class Command(pydantic.BaseModel):
    timestamp: float = pydantic.Field(default_factory=utc_now)
    user: str
    message: Optional[str]

    class Config:
        arbitrary_types_allowed = True
        extra = "forbid"
        alias_generator = alias_generators.to_lower_camel

    def serialize(self) -> dict:
        """Export as dict with alias and without None:s."""

        return self.dict(by_alias=True, exclude_none=True)
