import abc  # noqa: D100, I001
from typing import Optional  # noqa: F401

import pydantic
from karp.search.application.repositories import IndexEntry
from karp.lex_core.value_objects import unique_id  # noqa: F401


class PreviewEntryInputDto(pydantic.BaseModel):  # noqa: D101
    resource_id: str
    entry: dict
    user: str


class EntryPreviewDto(pydantic.BaseModel):  # noqa: D101
    entry: IndexEntry


class PreviewEntry(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def query(self, input_dto: PreviewEntryInputDto) -> EntryPreviewDto:  # noqa: D102
        ...
