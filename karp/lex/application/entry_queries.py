import typing  # noqa: I001

from sb_json_tools import jsondiff
import logging

from karp.lex.domain import errors

from karp.lex.domain.entities import Entry
from karp.lex.domain.dtos import EntryDto
from karp.lex.application.dtos import (
    EntryDiffDto,
    EntryHistoryRequest,
    EntryDiffRequest,
    GetHistoryDto,
    HistoryDto,
)
from karp.foundation.value_objects import UniqueId, UniqueIdStr
from ..infrastructure.sql import ResourceRepository
from injector import inject
from karp import plugins
from karp.plugins import Plugins

logger = logging.getLogger(__name__)


class EntryQueries:
    @inject
    def __init__(
        self,
        resources: ResourceRepository,
        plugins: Plugins,
    ) -> None:
        super().__init__()
        self.resources = resources
        self.plugins = plugins

    def _to_dtos(
        self, resource_id, entries: typing.Iterator[Entry]
    ) -> typing.Iterator[EntryDto]:
        resource = self.resources.by_resource_id(resource_id)
        return plugins.transform_entries(
            self.plugins, resource.config, (EntryDto.from_entry(entry) for entry in entries)
        )

    def _to_dto(self, entry: Entry) -> EntryDto:
        return next(self._to_dtos(entry.resource_id, [entry]))

    def by_id(
        self,
        resource_id: str,
        id: UniqueIdStr,  # noqa: A002
    ) -> EntryDto:
        entries = self.resources.entries_by_resource_id(resource_id)
        return self._to_dto(entries.by_id(UniqueId.validate(id)))

    def by_id_optional(
        self,
        resource_id: str,
        id: UniqueIdStr,  # noqa: A002
    ) -> typing.Optional[EntryDto]:
        entries = self.resources.entries_by_resource_id(resource_id)
        if entry := entries.by_id_optional(UniqueId.validate(id)):
            return self._to_dto(entry)
        return None

    def all_entries(self, resource_id: str) -> typing.Iterable[EntryDto]:
        entries = self.resources.entries_by_resource_id(resource_id)
        return self._to_dtos(resource_id, entries.all_entries())

    def get_entry_history(
        self,
        resource_id: str,
        id: UniqueIdStr,  # noqa: A002
        version: typing.Optional[int],
    ) -> EntryDto:
        entries = self.resources.entries_by_resource_id(resource_id)
        result = entries.by_id(UniqueId.validate(id), version=version)
        return self._to_dto(result)

    def get_history(
        self,
        request: EntryHistoryRequest,
    ) -> GetHistoryDto:
        logger.info("querying history", extra={"request": request})
        entries = self.resources.entries_by_resource_id(request.resource_id)
        paged_query, total = entries.get_history(
            entry_id=request.entry_id,
            user_id=request.user_id,
            from_date=request.from_date,
            to_date=request.to_date,
            from_version=request.from_version,
            to_version=request.to_version,
            offset=request.current_page * request.page_size,
            limit=request.page_size,
        )
        result = []
        previous_body: dict[str, typing.Any] = {}
        for history_entry in paged_query:
            # TODO fix this, we should get the diff in another way, probably store the diffs directly in the database
            # entry_version = history_entry.version
            # if entry_version > 1:
            #     previous_entry = entries.by_entry_id(
            #         history_entry.entry_id, version=entry_version - 1
            #     )
            #     previous_body = previous_entry.body
            # else:
            #     previous_body = {}
            history_diff = jsondiff.compare(previous_body, history_entry.body)
            logger.debug("diff", extra={"diff": history_diff})
            result.append(
                HistoryDto(
                    timestamp=history_entry.last_modified,
                    message=history_entry.message or "",
                    id=history_entry.entity_id,
                    version=history_entry.version,
                    op=history_entry.op,
                    userId=history_entry.last_modified_by,
                    diff=history_diff,
                    entry=history_entry.body,
                )
            )
            previous_body = history_entry.body

        return GetHistoryDto(history=result, total=total)

    def get_entry_diff(
        self,
        request: EntryDiffRequest,
    ) -> EntryDiffDto:
        entries = self.resources.entries_by_resource_id(request.resource_id)
        db_entry = entries.by_id(request.id)

        if request.from_version:
            obj1 = entries.by_id(db_entry.id, version=request.from_version)
        elif request.from_date is not None:
            obj1 = entries.by_id(db_entry.id, after_date=request.from_date)
        else:
            obj1 = entries.by_id(db_entry.id, oldest_first=True)

        obj1_body = obj1.body if obj1 else None

        if request.to_version:
            obj2 = entries.by_id(db_entry.id, version=request.to_version)
            obj2_body = obj2.body
        elif request.to_date is not None:
            obj2 = entries.by_id(db_entry.id, before_date=request.to_date)
            obj2_body = obj2.body
        elif request.entry is not None:
            obj2 = None
            obj2_body = request.entry
        else:
            obj2 = db_entry
            obj2_body = db_entry.body

        if obj1_body is None or obj2_body is None:
            raise errors.DiffImposible("diff impossible!")

        return EntryDiffDto(
            diff=jsondiff.compare(obj1_body, obj2_body),
            fromVersion=obj1.version,
            toVersion=obj2.version if obj2 else None,
        )
