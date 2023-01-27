import abc
from typing import Optional

import pydantic
from karp.search.application.repositories import IndexEntry
from karp.foundation.value_objects import unique_id


class PreviewEntryInputDto(pydantic.BaseModel):
    resource_id: str
    entry: dict
    user: str


class EntryPreviewDto(pydantic.BaseModel):
    entry: IndexEntry


class PreviewEntry(abc.ABC):
    @abc.abstractmethod
    def query(self, input_dto: PreviewEntryInputDto) -> EntryPreviewDto:
        ...
