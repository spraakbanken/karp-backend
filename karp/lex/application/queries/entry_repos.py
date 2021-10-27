import abc
from typing import Iterable

import pydantic


class EntryRepoDto(pydantic.BaseModel):
    name: str
    id: str


class ListEntryRepos(abc.ABC):
    @abc.abstractmethod
    def query(self) -> Iterable[EntryRepoDto]:
        pass
