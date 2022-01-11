import abc
from typing import Iterable

import pydantic

from karp.foundation.value_objects import UniqueId

class EntryRepoDto(pydantic.BaseModel):
    name: str
    id: UniqueId
    repository_type: str


class ListEntryRepos(abc.ABC):
    @abc.abstractmethod
    def query(self) -> Iterable[EntryRepoDto]:
        pass
