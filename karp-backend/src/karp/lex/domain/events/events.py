from typing import Dict  # noqa: D100

from karp.foundation import events, time
from karp.lex_core import alias_generators
from karp.lex_core.value_objects import unique_id
from pydantic import BaseModel


class Event(events.Event, BaseModel):  # noqa: D101
    timestamp: float

    class Config:  # noqa: D106
        arbitrary_types_allowed = True
        alias_generator = alias_generators.to_lower_camel


class AppStarted(Event):  # noqa: D101
    def __init__(self):  # noqa: D107, ANN204
        self.timestamp = time.utc_now()


class IdMixin(BaseModel):  # noqa: D101
    id: unique_id.UniqueIdStr  # noqa: A003


class ResourceCreated(IdMixin, Event):
    """Event emitted when a resource is created."""

    resource_id: str
    entry_repo_id: unique_id.UniqueIdStr
    name: str
    config: dict
    user: str
    message: str


# class ResourceLoaded(Event):
#     entity_id: unique_id.UniqueIdStr
#     resource_id: str
#     name: str
#     config: dict
#     user: str
#     message: str
#     version: int


class ResourceDiscarded(IdMixin, Event):  # noqa: D101
    resource_id: str
    name: str
    config: dict
    user: str
    message: str
    version: int


class ResourcePublished(IdMixin, Event):  # noqa: D101
    resource_id: str
    entry_repo_id: unique_id.UniqueIdStr
    version: int
    name: str
    config: Dict
    user: str
    message: str


class ResourceUpdated(IdMixin, Event):  # noqa: D101
    resource_id: str
    entry_repo_id: unique_id.UniqueIdStr
    version: int
    name: str
    config: dict
    user: str
    message: str


class EntryAdded(IdMixin, Event):  # noqa: D101
    repo_id: unique_id.UniqueIdStr
    body: dict
    message: str
    user: str


class EntryUpdated(IdMixin, Event):  # noqa: D101
    repo_id: unique_id.UniqueIdStr
    body: dict
    message: str
    user: str
    version: int


class EntryDeleted(IdMixin, Event):  # noqa: D101
    repo_id: unique_id.UniqueIdStr
    version: int
    message: str
    user: str
