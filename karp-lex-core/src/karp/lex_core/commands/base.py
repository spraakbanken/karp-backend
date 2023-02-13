from datetime import datetime, timezone

import pydantic


def utc_now() -> float:
    """A UTC timestamp in seconds.

    This function may return the same timestamp twice.
    """
    return datetime.now(timezone.utc).timestamp()


class Command(pydantic.BaseModel):
    timestamp: float = pydantic.Field(default_factory=utc_now)

    class Config:
        arbitrary_types_allowed = True
