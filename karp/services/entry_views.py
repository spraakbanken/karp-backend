import typing

import pydantic

from sb_json_tools import jsondiff

from karp.domain import model
from karp.utility import unique_id
from . import context


def get_by_id(
    resource_id: str, entry_uuid: unique_id.UniqueId, ctx: context.Context
) -> typing.Optional[model.Entry]:
    with ctx.entry_uows.get_uow(resource_id) as uow:
        return uow.repo.by_id(entry_uuid)


def get_by_entry_id(
    resource_id: str, entry_id: str, ctx: context.Context
) -> typing.Optional[model.Entry]:
    with ctx.entry_uows.get_uow(resource_id) as uow:
        return uow.repo.by_entry_id(entry_id)


def get_entry_history(
    resource_id: str, entry_id: str, version: typing.Optional[int], ctx: context.Context
):
    # with ctx.resource_uow as uw:
    #     resource = uw.repo.by_resource_id(resource_id)
    with ctx.entry_uows.get_uow(resource_id) as uw:
        result = uw.repo.by_entry_id(entry_id, version=version)

    return {
        "entry_id": entry_id,
        "resource": resource_id,
        "version": version,
        "entry": result.body,
        "last_modified_by": result.last_modified_by,
        "last_modified": result.last_modified,
    }


class EntryHistoryRequest(pydantic.BaseModel):
    user_id: typing.Optional[str] = None
    entry_id: typing.Optional[str] = None
    from_date: typing.Optional[float] = None
    to_date: typing.Optional[float] = None
    from_version: typing.Optional[int] = None
    to_version: typing.Optional[int] = None
    current_page: int = 0
    page_size: int = 100


def get_history(
    resource_id: str,
    history_request: EntryHistoryRequest,
    # user_id: Optional[str] = None,
    # entry_id: Optional[str] = None,
    # from_date: Optional[float] = None,
    # to_date: Optional[float] = None,
    # from_version: Optional[int] = None,
    # to_version: Optional[int] = None,
    # current_page: int = 0,
    # page_size: int = 100,
    ctx: context.Context,
):
    # with unit_of_work(using=ctx.resource_repo) as uw:
    #     resource = uw.get_active_resource(resource_id)

    with ctx.entry_uows.get_uow(resource_id) as uw:
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
