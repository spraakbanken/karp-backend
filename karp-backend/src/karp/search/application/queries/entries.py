import abc  # noqa: D100, I001
from typing import Optional  # noqa: F401

import pydantic
from karp.search.application.repositories import IndexEntry
from karp.lex_core import alias_generators


class BaseModel(pydantic.BaseModel):  # noqa: D101
    class Config:  # noqa: D106
        # arbitrary_types_allowed = True
        alias_generator = alias_generators.to_lower_camel


class PreviewEntryInputDto(BaseModel):  # noqa: D101
    resource_id: str
    entry: dict
    user: str


class EntryPreviewDto(BaseModel):  # noqa: D101
    entry: IndexEntry


class PreviewEntry(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def query(self, input_dto: PreviewEntryInputDto) -> EntryPreviewDto:  # noqa: D102
        ...
