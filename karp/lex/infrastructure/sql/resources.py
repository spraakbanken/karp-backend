import logging
import typing
from typing import List, Optional, Union

import sqlalchemy as sa
from injector import inject
from sqlalchemy import Engine, and_, func, sql, text
from sqlalchemy.orm import Session

from karp.foundation import repository
from karp.foundation.cache import Cache
from karp.foundation.value_objects import UniqueId
from karp.lex.domain import entities
from karp.lex.domain.entities.resource import Resource
from karp.lex.domain.errors import ResourceNotFound

from .entries import EntryRepository
from .models import ResourceModel

logger = logging.getLogger(__name__)


class ResourceRepository(repository.Repository):
    EntityNotFound = ResourceNotFound

    @inject
    def __init__(self, session: Session):
        self._session = session
        # caches lookups to self._by_resource_id
        # Note: we ought to also invalidate the cache if a transaction is rolled back.
        # It's OK right now because after rolling back we always end the session, so
        # the SqlResourceRepository itself is no longer valid.
        self._cache = Cache(self._by_resource_id_uncached)

    def by_resource_id(
        self, resource_id: str, *, version: Optional[int] = None
    ) -> entities.Resource:
        if resource := self.by_resource_id_optional(resource_id, version=version):
            return resource
        else:
            raise self.EntityNotFound(f"Entity with resource_id='{resource_id}' can't be found.")

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
                func.max(ResourceModel.last_modified).label("maxdate"),
            )
            .group_by(ResourceModel.resource_id)
            .subquery("t2")
        )
        query = self._session.query(ResourceModel).join(
            subq,
            and_(
                ResourceModel.resource_id == subq.c.resource_id,
                ResourceModel.last_modified == subq.c.maxdate,
                ResourceModel.is_published == True,  # noqa: E712
            ),
        )

        return [resource_dto.to_entity() for resource_dto in query if resource_dto is not None]

    def get_all_resources(self) -> typing.List[entities.Resource]:
        subq = (
            self._session.query(
                ResourceModel.resource_id,
                func.max(ResourceModel.last_modified).label("maxdate"),
            )
            .group_by(ResourceModel.resource_id)
            .subquery("t2")
        )
        query = self._session.query(ResourceModel).join(
            subq,
            and_(
                ResourceModel.resource_id == subq.c.resource_id,
                ResourceModel.last_modified == subq.c.maxdate,
            ),
        )

        return [resource_dto.to_entity() for resource_dto in query if resource_dto is not None]

    def delete_all_versions(self, resource_id):
        query = self._session.query(ResourceModel).filter_by(resource_id=resource_id)
        for resource in query:
            self._session.delete(resource)

    def remove_resource_table(self, resource):
        self._session.execute(text("DROP TABLE IF EXISTS " + resource.table_name))

    def remove(self, resource: Resource):
        self._session.delete(resource)

    def _save(self, resource: Resource):
        resource_dto = ResourceModel.from_entity(resource)
        self._session.add(resource_dto)
        # If resource was discarded, drop the table containing all data entries.
        # Otherwise, create the table.
        entry_repo = EntryRepository(self._session, resource)
        if resource.discarded:
            entry_repo.drop_table()
        else:
            entry_repo.create_table()

        self._cache.clear()

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

    def _by_resource_id(
        self,
        resource_id: str,
    ) -> Optional[Resource]:
        return self._cache[resource_id]

    def _by_resource_id_uncached(
        self,
        resource_id: str,
    ) -> Optional[Resource]:
        subq = (
            sql.select(
                ResourceModel.entity_id,
                sa.func.max(ResourceModel.last_modified).label("maxdate"),
            )
            .group_by(ResourceModel.entity_id)
            .subquery("t2")
        )

        stmt = sql.select(ResourceModel).join(
            subq,
            sa.and_(
                ResourceModel.entity_id == subq.c.entity_id,
                ResourceModel.last_modified == subq.c.maxdate,
                ResourceModel.resource_id == resource_id,
            ),
        )
        stmt = stmt.order_by(ResourceModel.last_modified.desc())

        query = self._session.execute(stmt).scalars()
        resource_dto = query.first()
        return resource_dto.to_entity() if resource_dto else None

    def entries_by_resource_id(self, resource_id: str) -> Optional[EntryRepository]:
        resource = self.by_resource_id(resource_id)
        return EntryRepository(session=self._session, resource=resource) if resource else None
