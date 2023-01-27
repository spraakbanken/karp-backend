import abc
from typing import Iterable, Optional

import pydantic

from karp.foundation.value_objects import UniqueIdStr


class EntryRepoDto(pydantic.BaseModel):
    name: str
    entity_id: UniqueIdStr
    repository_type: str


class ListEntryRepos(abc.ABC):
    @abc.abstractmethod
    def query(self) -> Iterable[EntryRepoDto]:
        pass


class ReadOnlyEntryRepoRepositry(abc.ABC):
    @abc.abstractmethod
    def get_by_name(self, name: str) -> Optional[EntryRepoDto]:
        pass
