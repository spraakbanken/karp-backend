import logging
import typing
from typing import Optional, Union

import methodtools
import sqlalchemy as sa
from injector import inject
from sqlalchemy import and_, func, sql
from sqlalchemy.orm import Session

from karp.foundation.value_objects import UniqueId
from karp.lex.domain import entities
from karp.lex.domain.entities.resource import Resource
from karp.lex.domain.errors import ResourceNotFound

from .entries import EntryRepository
from .models import ResourceModel

logger = logging.getLogger(__name__)


class ResourceRepository:
    @inject
    def __init__(self, session: Session):
        self._session = session

    def by_id(
        self,
        id: UniqueId,  # noqa: A002
        *,
        version: Optional[int] = None,
        **kwargs,
    ):
        if entity := self._by_id(id, version=version):
            return entity
        raise ResourceNotFound(f"Entity with id={id} is not found")

    def by_id_optional(
        self,
        id: UniqueId,  # noqa: A002
        *,
        version: Optional[int] = None,
        **kwargs,
    ) -> Optional:
        return self._by_id(id, version=version)

    def by_resource_id(self, resource_id: str, *, version: Optional[int] = None) -> entities.Resource:
        if resource := self.by_resource_id_optional(resource_id, version=version):
            return resource
        else:
            raise ResourceNotFound(f"Resource with resource_id='{resource_id}' can't be found.")

    def by_resource_id_optional(
        self, resource_id: str, *, version: Optional[int] = None
    ) -> typing.Optional[entities.Resource]:
        resource = self._by_resource_id(resource_id)
        if not resource:
            return None

        if version:
            resource = self._by_id(resource.entity_id, version=version)
        return resource

    def get_published_resources(self) -> typing.List[entities.Resource]:
        subq = (
            self._session.query(
                ResourceModel.resource_id,
                func.max(ResourceModel.history_id).label("history_id"),
            )
            .group_by(ResourceModel.resource_id)
            .subquery("t2")
        )
        query = self._session.query(ResourceModel).join(
            subq,
            and_(
                ResourceModel.resource_id == subq.c.resource_id,
                ResourceModel.history_id == subq.c.history_id,
                ResourceModel.is_published == True,  # noqa: E712
            ),
        )

        return [resource_dto.to_entity() for resource_dto in query if resource_dto is not None]

    def get_all_resources(self) -> typing.List[entities.Resource]:
        subq = (
            self._session.query(
                ResourceModel.resource_id,
                func.max(ResourceModel.history_id).label("history_id"),
            )
            .group_by(ResourceModel.resource_id)
            .subquery("t2")
        )
        query = self._session.query(ResourceModel).join(
            subq,
            and_(
                ResourceModel.resource_id == subq.c.resource_id,
                ResourceModel.history_id == subq.c.history_id,
            ),
        )

        return [resource_dto.to_entity() for resource_dto in query if resource_dto is not None]

    def delete_all_versions(self, resource_id):
        query = self._session.query(ResourceModel).filter_by(resource_id=resource_id)
        for resource in query:
            self._session.delete(resource)

    def create_resource_table(self, resource):
        EntryRepository(self._session, resource).create_table()

    def remove_resource_table(self, resource):
        EntryRepository(self._session, resource).drop_table()

    def save(self, resource: Resource):
        resource_dto = ResourceModel.from_entity(resource)
        self._session.add(resource_dto)
        # If resource was discarded, drop the table containing all data entries.
        # Otherwise, create the table.
        if resource.discarded:
            self.remove_resource_table(resource)
        else:
            self.create_resource_table(resource)

        self._by_resource_id.cache_clear()

    def _by_id(
        self,
        uid: Union[UniqueId, str],
        *,
        version: Optional[int] = None,
        **kwargs,
    ) -> typing.Optional[entities.Resource]:
        query = self._session.query(ResourceModel).filter_by(entity_id=uid)
        if version:
            query = query.filter_by(version=version)
        else:
            query = query.order_by(ResourceModel.version.desc())
        resource_dto = query.first()
        return resource_dto.to_entity() if resource_dto else None

    # Note: we ought to also invalidate the cache if a transaction is rolled back.
    # It's OK right now because after rolling back we always end the session, so
    # the SqlResourceRepository itself is no longer valid.
    @methodtools.lru_cache(maxsize=None)
    def _by_resource_id(
        self,
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

        query = self._session.execute(stmt).scalars()
        resource_dto = query.first()
        return resource_dto.to_entity() if resource_dto else None

    def entries_by_resource_id(self, resource_id: str) -> EntryRepository:
        resource = self.by_resource_id(resource_id)
        return EntryRepository(session=self._session, resource=resource)
