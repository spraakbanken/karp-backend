import logging
import typing
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import and_, func, sql

from karp.foundation.value_objects import UniqueId
from karp.globals import session
from karp.lex.domain import entities
from karp.lex.domain.entities.resource import Resource
from karp.lex.domain.errors import ResourceNotFound

from .entries import EntryRepository
from .models import ResourceModel

logger = logging.getLogger(__name__)


def by_resource_id(resource_id: str, *, version: Optional[int] = None) -> entities.Resource:
    if resource := by_resource_id_optional(resource_id, version=version):
        return resource
    else:
        raise ResourceNotFound(f"Resource with resource_id='{resource_id}' can't be found.")


def by_resource_id_optional(resource_id: str, *, version: Optional[int] = None) -> typing.Optional[entities.Resource]:
    resource = _by_resource_id(resource_id)
    if not resource:
        return None

    if version:
        resource = _by_id(resource.entity_id, version=version)
    return resource


def get_published_resource_ids() -> list[str]:
    return [resource.resource_id for resource in get_published_resources()]


def get_published_resources() -> typing.List[entities.Resource]:
    subq = (
        session.query(
            ResourceModel.resource_id,
            func.max(ResourceModel.history_id).label("history_id"),
        )
        .group_by(ResourceModel.resource_id)
        .subquery("t2")
    )
    query = session.query(ResourceModel).join(
        subq,
        and_(
            ResourceModel.resource_id == subq.c.resource_id,
            ResourceModel.history_id == subq.c.history_id,
            ResourceModel.is_published == True,  # noqa: E712
        ),
    )

    return [resource_dto.to_entity() for resource_dto in query if resource_dto is not None]


def get_all_resources() -> typing.List[entities.Resource]:
    subq = (
        session.query(
            ResourceModel.resource_id,
            func.max(ResourceModel.history_id).label("history_id"),
        )
        .group_by(ResourceModel.resource_id)
        .subquery("t2")
    )
    query = session.query(ResourceModel).join(
        subq,
        and_(
            ResourceModel.resource_id == subq.c.resource_id,
            ResourceModel.history_id == subq.c.history_id,
        ),
    )

    return [resource_dto.to_entity() for resource_dto in query if resource_dto is not None]


def delete_all_versions(resource_id):
    query = session.query(ResourceModel).filter_by(resource_id=resource_id)
    for resource in query:
        session.delete(resource)


def create_resource_table(resource):
    EntryRepository(resource).create_table()


def remove_resource_table(resource):
    EntryRepository(resource).drop_table()


def save(resource: Resource):
    resource_dto = ResourceModel.from_entity(resource)
    session.add(resource_dto)
    # If resource was discarded, drop the table containing all data entries.
    # Otherwise, create the table.
    if resource.discarded:
        remove_resource_table(resource)
    else:
        create_resource_table(resource)


def _by_id(uid: UniqueId | str, version: int | None = None) -> entities.Resource | None:
    query = session.query(ResourceModel).filter_by(entity_id=uid)
    if version:
        query = query.filter_by(version=version)
    else:
        query = query.order_by(ResourceModel.version.desc())
    resource_dto = query.first()
    return resource_dto.to_entity() if resource_dto else None


def _by_resource_id(
    resource_id: str,
) -> Optional[Resource]:
    subq = (
        sql.select(
            ResourceModel.entity_id,
            sa.func.max(ResourceModel.history_id).label("history_id"),
        )
        .group_by(ResourceModel.entity_id)
        .subquery("t2")
    )

    stmt = sql.select(ResourceModel).join(
        subq,
        sa.and_(
            ResourceModel.entity_id == subq.c.entity_id,
            ResourceModel.history_id == subq.c.history_id,
            ResourceModel.resource_id == resource_id,
        ),
    )
    stmt = stmt.order_by(ResourceModel.history_id.desc())

    query = session.execute(stmt).scalars()
    resource_dto = query.first()
    return resource_dto.to_entity() if resource_dto else None


def entries_by_resource_id(resource_id: str) -> EntryRepository:
    resource = by_resource_id(resource_id)
    return EntryRepository(resource=resource)
