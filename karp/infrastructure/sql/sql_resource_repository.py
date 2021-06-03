"""SQL Resource Repository"""
import logging
from typing import Optional, List, Tuple, Dict, Union
from uuid import UUID
import typing

from karp.domain.errors import RepositoryStatusError, IntegrityError
from karp.domain.models.resource import (
    Resource,
    ResourceOp,
)
from karp.domain import model, repository, errors

from . import db, sql_models
from .sql_models import ResourceDTO
from .sql_repository import SqlRepository

_logger = logging.getLogger("karp")


class SqlResourceRepository(SqlRepository, repository.ResourceRepository):
    def __init__(self, session=None):
        repository.ResourceRepository.__init__(self)
        SqlRepository.__init__(self)
        self.table = sql_models.ResourceDTO
        self._session = session

    def check_status(self):
        self._check_has_session()
        try:
            self._session.execute("SELECT 1")
        except db.SQLAlchemyError as err:
            _logger.exception(str(err))
            raise errors.RepositoryStatusError("Database error") from err

    @classmethod
    def primary_key(cls):
        return "resource_id"

    def _put(self, resource: Resource):
        self._check_has_session()
        # Check if resource exists
        existing_resource = self.by_resource_id(resource.resource_id)
        if (
            existing_resource
            and not existing_resource.discarded
            and existing_resource.id != resource.id
        ):
            raise errors.IntegrityError(
                f"Resource with resource_id '{resource.resource_id}' already exists."
            )
        if resource.version is None:
            resource._version = self.get_latest_version(resource.resource_id) + 1

        # self._session.execute(
        #     db.insert(self.table).values(**self._resource_to_dict(resource))
        # )
        resource_dto = ResourceDTO.from_entity(resource)
        self._session.add(resource_dto)

    _update = _put

    def resource_ids(self) -> List[str]:
        self._check_has_session()
        query = self._session.query(ResourceDTO)
        return [row.resource_id for row in query.group_by(self.table.resource_id).all()]

    def _by_id(
        self, id: Union[UUID, str], *, version: Optional[int] = None
    ) -> typing.Optional[model.Resource]:
        self._check_has_session()
        query = self._session.query(ResourceDTO).filter_by(id=id)
        if version:
            query = query.filter_by(version=version)
        else:
            query = query.order_by(ResourceDTO.version.desc())
        resource_dto = query.first()
        return resource_dto.to_entity() if resource_dto else None

    def _by_resource_id(
        self, resource_id: str, *, version: Optional[int] = None
    ) -> Optional[Resource]:
        self._check_has_session()
        query = self._session.query(ResourceDTO).filter_by(resource_id=resource_id)
        if version:
            query = query.filter_by(version=version)
        else:
            query = query.order_by(ResourceDTO.version.desc())
        resource_dto = query.first()
        return resource_dto.to_entity() if resource_dto else None

    def resources_with_id(self, resource_id: str):
        pass

    def resource_with_id_and_version(
        self, resource_id: str, version: int
    ) -> Optional[Resource]:
        self._check_has_session()
        query = self._session.query(ResourceDTO)
        resource_dto = query.filter_by(resource_id=resource_id, version=version).first()
        return resource_dto.to_entity() if resource_dto else None

    def get_active_resource(self, resource_id: str) -> Optional[Resource]:
        self._check_has_session()
        query = self._session.query(self.table)
        resource_dto = query.filter_by(
            resource_id=resource_id, is_published=True
        ).one_or_none()
        return resource_dto.to_entity()

    def get_latest_version(self, resource_id: str) -> int:
        self._check_has_session()
        row = (
            self._session.query(self.table)
            .order_by(self.table.version.desc())
            .filter_by(resource_id=resource_id)
            .first()
        )
        if row is None:
            return 0
        return row.version

    def history_by_resource_id(self, resource_id: str) -> typing.List[model.Resource]:
        self._check_has_session()
        query = self._session.query(ResourceDTO)
        return [
            resource_dto.to_entity()
            for resource_dto in query.filter_by(resource_id=resource_id)
            .order_by(ResourceDTO.version.desc())
            .all()
        ]

    def _get_published_resources(self) -> typing.List[model.Resource]:
        self._check_has_session()
        subq = (
            self._session.query(
                ResourceDTO.resource_id,
                db.func.max(ResourceDTO.last_modified).label("maxdate"),
            )
            .group_by(ResourceDTO.resource_id)
            .subquery("t2")
        )
        query = self._session.query(ResourceDTO).join(
            subq,
            db.and_(
                ResourceDTO.resource_id == subq.c.resource_id,
                ResourceDTO.last_modified == subq.c.maxdate,
                ResourceDTO.is_published == True,
            ),
        )

        return [
            resource_dto.to_entity()
            for resource_dto in query
            if resource_dto is not None
        ]

    def _resource_to_dict(self, resource: Resource) -> typing.Dict:
        return {
            "history_id": None,
            "id": resource.id,
            "resource_id": resource.resource_id,
            "version": resource.version,
            "name": resource.name,
            "config": resource.config,
            "is_published": resource.is_published,
            "last_modified": resource.last_modified,
            "last_modified_by": resource.last_modified_by,
            "message": resource.message,
            "op": resource.op,
            "discarded": resource.discarded,
        }
    # def _resource_to_row(
    #     self, resource: Resource
    # ) -> Tuple[
    #     None,
    #     UUID,
    #     str,
    #     int,
    #     str,
    #     Dict,
    #     Optional[bool],
    #     float,
    #     str,
    #     str,
    #     ResourceOp,
    #     bool,
    # ]:
    #     # config = resource.config
    #     resource.config["entry_repository_type"] = resource.entry_repository_type
    #     resource.config[
    #         "entry_repository_settings"
    #     ] = resource.entry_repository_settings
    #     return (
    #         None,
    #         resource.id,
    #         resource.resource_id,
    #         resource.version,
    #         resource.name,
    #         resource.config,
    #         resource.is_published,
    #         resource.last_modified,
    #         resource.last_modified_by,
    #         resource.message,
    #         resource.op,
    #         resource.discarded,
    #     )

    # def _row_to_resource(self, row) -> Resource:
    #     entry_repository_type = row.config.pop("entry_repository_type")
    #     entry_respsitory_settings = row.config.pop("entry_repository_settings")
    #     return Resource(
    #         entity_id=row.id,
    #         resource_id=row.resource_id,
    #         version=row.version,
    #         name=row.name,
    #         config=row.config,
    #         message=row.message,
    #         op=row.op,
    #         is_published=row.is_published,
    #         last_modified=row.last_modified,
    #         last_modified_by=row.last_modified_by,
    #         discarded=row.discarded,
    #         entry_repository_type=entry_repository_type,
    #         entry_repository_settings=entry_respsitory_settings,
    #     )
