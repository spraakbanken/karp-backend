import abc  # noqa: D100, I001
import typing

import pydantic

from karp.lex_core import alias_generators
from karp.lex_core.value_objects import unique_id

from karp.lex.domain.entities.entry import EntryOp


class BaseModel(pydantic.BaseModel):  # noqa: D101
    class Config:  # noqa: D106
        # arbitrary_types_allowed = True
        extra = "forbid"
        alias_generator = alias_generators.to_lower_camel


class IdMixin(BaseModel):  # noqa: D101
    id: unique_id.UniqueIdStr  # noqa: A003


class EntryDto(IdMixin, BaseModel):  # noqa: D101
    resource: str
    version: int
    entry: typing.Dict
    last_modified: float
    last_modified_by: str
    message: str | None = None
    discarded: bool = False


class EntryDiffRequest(IdMixin, BaseModel):  # noqa: D101
    resource_id: str
    from_version: typing.Optional[int] = None
    to_version: typing.Optional[int] = None
    from_date: typing.Optional[float] = None
    to_date: typing.Optional[float] = None
    entry: typing.Optional[typing.Dict] = None


class EntryHistoryRequest(BaseModel):  # noqa: D101
    resource_id: str
    user_id: typing.Optional[str] = None
    entry_id: typing.Optional[unique_id.UniqueIdStr] = None
    from_date: typing.Optional[float] = None
    to_date: typing.Optional[float] = None
    from_version: typing.Optional[int] = None
    to_version: typing.Optional[int] = None
    current_page: int = 0
    page_size: int = 100


class EntryDiffDto(BaseModel):  # noqa: D101
    diff: typing.Any
    from_version: typing.Optional[int]
    to_version: typing.Optional[int]


class HistoryDto(IdMixin, BaseModel):  # noqa: D101
    timestamp: float
    message: str
    version: int
    op: EntryOp
    user_id: str
    diff: list[dict]


class GetEntryDiff(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def query(self, request: EntryDiffRequest) -> EntryDiffDto:  # noqa: D102
        pass


class GetEntryHistory(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def query(  # noqa: D102
        self,
        resource_id: str,
        entity_id: unique_id.UniqueIdStr,
        # entry_id: str,
        version: typing.Optional[int],
    ) -> EntryDto:
        pass


class GetHistoryDto(BaseModel):  # noqa: D101
    history: list[HistoryDto]
    total: int


class GetHistory(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def query(self, request: EntryHistoryRequest) -> GetHistoryDto:  # noqa: D102
        pass


class EntryViews(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def get_by_id(  # noqa: D102
        self,
        resource_id: str,
        entity_id: unique_id.UniqueIdStr,
    ) -> EntryDto:
        pass

    @abc.abstractmethod
    def get_by_id_optional(  # noqa: D102
        self,
        resource_id: str,
        entity_id: unique_id.UniqueIdStr,
    ) -> typing.Optional[EntryDto]:
        pass

    # @abc.abstractmethod
    # def get_by_entry_id(
    #     self,
    #     resource_id: str,
    #     entry_id: str,
    # ) -> EntryDto:
    #     pass

    # @abc.abstractmethod
    # def get_by_entry_id_optional(
    #     self,
    #     resource_id: str,
    #     entry_id: str,
    # ) -> typing.Optional[EntryDto]:
    #     pass

    @abc.abstractmethod
    def get_total(self, resource_id: str) -> int:  # noqa: D102
        pass

    @abc.abstractmethod
    def get_by_referenceable(  # noqa: D102
        self, resource_id: str, filters
    ) -> typing.Iterable[EntryDto]:
        pass

    @abc.abstractmethod
    def all_entries(self, resource_id: str) -> typing.Iterable[EntryDto]:  # noqa: D102
        pass
