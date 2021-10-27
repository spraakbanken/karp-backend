import abc
from typing import Iterable

import pydantic


class ResourceDto(pydantic.BaseModel):
    resource_id: str
    id: str
    published: bool
    version: int
    last_modified: float


class GetPublishedResources(abc.ABC):
    @abc.abstractmethod
    def query(self) -> Iterable[ResourceDto]:
        pass

