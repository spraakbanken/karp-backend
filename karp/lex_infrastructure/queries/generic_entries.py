import typing

from sb_json_tools import jsondiff

from karp.lex.domain.entities import Entry
from karp.lex.application.queries import EntryViews, EntryDto, EntryDiffDto, GetEntryDiff, GetEntryHistory, GetHistory, EntryHistoryRequest, EntryDiffRequest
from karp.foundation.value_objects import unique_id
from karp.lex.application.repositories.entry_repositories import EntryUowRepositoryUnitOfWork
from karp.lex.application.repositories.unit_of_work import ResourceUnitOfWork


class GenericEntryViews(EntryViews):
    def __init__(
        self,
        resource_uow: ResourceUnitOfWork,
        entry_uow_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> None:
        super().__init__()
        self._resource_uow = resource_uow
        self.entry_uow_repo_uow = entry_uow_repo_uow

    def get_by_id(self, resource_id: str, entry_uuid: unique_id.UniqueId) -> EntryDto:
        with self._resource_uow as uw:
            entry_repo_id = uw.repo.by_resource_id(
                resource_id).entry_repository_id
        with self.entry_uow_repo_uow as uw:
            entry_uow = uw.repo.get_by_id(entry_repo_id)
        with entry_uow as uw:
            return self._entry_to_entry_dto(uw.repo.by_id(entry_uuid), resource_id)

    def get_by_entry_id(self, resource_id: str, entry_id: str) -> EntryDto:
        with self._resource_uow as uw:
            entry_repo_id = uw.repo.by_resource_id(
                resource_id).entry_repository_id
        with self.entry_uow_repo_uow as uw:
            entry_uow = uw.repo.get_by_id(entry_repo_id)
        with entry_uow as uw:
            return self._entry_to_entry_dto(uw.repo.by_entry_id(entry_id), resource_id)

    def _entry_to_entry_dto(self, entry: Entry, resource_id: str) -> EntryDto:
        return EntryDto(
            entry_id=entry.entry_id,
            entry_uuid=entry.id,
            resource=resource_id,
            version=entry.version,
            entry=entry.body,
            last_modified=entry.last_modified,
            last_modified_by=entry.last_modified_by,
        )


class GenericEntryQuery:
    def __init__(
        self,
        resource_uow: ResourceUnitOfWork,
        entry_uow_repo_uow: EntryUowRepositoryUnitOfWork,
    ):
        self._resource_uow = resource_uow
        self.entry_uow_repo_uow = entry_uow_repo_uow

    def get_entry_repo_id(self, resource_id: str) -> unique_id.UniqueId:
        with self._resource_uow as uw:
            return uw.repo.by_resource_id(resource_id).entry_repository_id


class GenericGetEntryHistory(GenericEntryQuery, GetEntryHistory):
    def query(
        self,
        resource_id: str,
        entry_id: str,
        version: typing.Optional[int],
    ) -> EntryDto:
        entry_repo_id = self.get_entry_repo_id(resource_id)
        with self.entry_uow_repo_uow, self.entry_uow_repo_uow.repo.get_by_id(entry_repo_id) as uw:
            result = uw.repo.by_entry_id(entry_id, version=version)

        return EntryDto(
            entry_id=entry_id,
            entry_uuid=result.id,
            resource=resource_id,
            version=version,
            entry=result.body,
            last_modified_by=result.last_modified_by,
            last_modified=result.last_modified,
        )


class GenericGetHistory(GenericEntryQuery, GetHistory):
    def query(
        self,
        history_request: EntryHistoryRequest,
    ):
        entry_repo_id = self.get_entry_repo_id(history_request.resource_id)
        with self.entry_uow_repo_uow, self.entry_uow_repo_uow.repo.get_by_id(entry_repo_id) as uw:
            paged_query, total = uw.repo.get_history(
                entry_id=history_request.entry_id,
                user_id=history_request.user_id,
                from_date=history_request.from_date,
                to_date=history_request.to_date,
                from_version=history_request.from_version,
                to_version=history_request.to_version,
                offset=history_request.current_page * history_request.page_size,
                limit=history_request.page_size,
            )
        result = []
        previous_body = {}
        for history_entry in paged_query:
            # TODO fix this, we should get the diff in another way, probably store the diffs directly in the database
            # entry_version = history_entry.version
            # if entry_version > 1:
            #     previous_entry = uw.repo.by_entry_id(
            #         history_entry.entry_id, version=entry_version - 1
            #     )
            #     previous_body = previous_entry.body
            # else:
            #     previous_body = {}
            history_diff = jsondiff.compare(previous_body, history_entry.body)
            result.append(
                {
                    "timestamp": history_entry.last_modified,
                    "message": history_entry.message or "",
                    "entry_id": history_entry.entry_id,
                    "version": history_entry.version,
                    "op": history_entry.op,
                    "user_id": history_entry.last_modified_by,
                    "diff": history_diff,
                }
            )
            previous_body = history_entry.body

        return result, total


class GenericGetEntryDiff(GenericEntryQuery, GetEntryDiff):
    def query(
        self,
        diff_request: EntryDiffRequest,
    ) -> EntryDiffDto:

        entry_repo_id = self.get_entry_repo_id(diff_request.resource_id)
        with self.entry_uow_repo_uow, self.entry_uow_repo_uow.repo.get_by_id(entry_repo_id) as uw:
            db_entry = uw.repo.by_entry_id(diff_request.entry_id)

            #     src = resource_obj.model.query.filter_by(entry_id=entry_id).first()
            #
            #     query = resource_obj.history_model.query.filter_by(entry_id=src.id)
            #     timestamp_field = resource_obj.history_model.timestamp
            #
            if diff_request.from_version:
                obj1 = uw.repo.by_id(
                    db_entry.id, version=diff_request.from_version)
            elif diff_request.from_date is not None:
                obj1 = uw.repo.by_id(
                    db_entry.id, after_date=diff_request.from_date)
            else:
                obj1 = uw.repo.by_id(db_entry.id, oldest_first=True)

            obj1_body = obj1.body if obj1 else None

            if diff_request.to_version:
                obj2 = uw.repo.by_id(
                    db_entry.id, version=diff_request.to_version)
                obj2_body = obj2.body
            elif diff_request.to_date is not None:
                obj2 = uw.repo.by_id(
                    db_entry.id, before_date=diff_request.to_date)
                obj2_body = obj2.body
            elif diff_request.entry is not None:
                obj2 = None
                obj2_body = diff_request.entry
            else:
                obj2 = db_entry
                obj2_body = db_entry.body

        #     elif from_date is not None:
        #         obj1_query = query.filter(timestamp_field >= from_date).order_by(
        #             timestamp_field
        #         )
        #     else:
        #         obj1_query = query.order_by(timestamp_field)
        #     if to_version:
        #         obj2_query = query.filter_by(version=to_version)
        #     elif to_date is not None:
        #         obj2_query = query.filter(timestamp_field <= to_date).order_by(
        #             timestamp_field.desc()
        #         )
        #     else:
        #         obj2_query = None
        #
        #     obj1 = obj1_query.first()
        #     obj1_body = json.loads(obj1.body) if obj1 else None
        #
        #     if obj2_query:
        #         obj2 = obj2_query.first()
        #         obj2_body = json.loads(obj2.body) if obj2 else None
        #     elif entry is not None:
        #         obj2 = None
        #         obj2_body = entry
        #     else:
        #         obj2 = query.order_by(timestamp_field.desc()).first()
        #         obj2_body = json.loads(obj2.body) if obj2 else None
        #
        if not obj1_body or not obj2_body:
            raise karp_errors.KarpError("diff impossible!")
        #
        return EntryDiffDto(
            diff=jsondiff.compare(obj1_body, obj2_body),
            from_version=obj1.version,
            to_version=obj2.version if obj2 else None,
        )
