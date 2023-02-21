import abc  # noqa: D100, I001
from typing import Iterable, Optional

import pydantic

from karp.lex_core.value_objects import UniqueIdStr


class EntryRepoDto(pydantic.BaseModel):  # noqa: D101
    name: str
    entity_id: UniqueIdStr
    repository_type: str


class ListEntryRepos(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def query(self) -> Iterable[EntryRepoDto]:  # noqa: D102
        pass


class ReadOnlyEntryRepoRepository(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def get_by_name(self, name: str) -> Optional[EntryRepoDto]:  # noqa: D102
        pass
