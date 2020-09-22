"""SQL Resource Repository"""
import logging
from typing import Optional, List, Tuple, Dict
from uuid import UUID

from karp.domain.errors import RepositoryStatusError
from karp.domain.models.resource import (
    Resource,
    ResourceOp,
    ResourceRepository,
)

from karp.infrastructure.sql import db
from karp.infrastructure.sql.sql_repository import SqlRepository

_logger = logging.getLogger("karp")


class SqlResourceRepository(ResourceRepository, SqlRepository):
    def __init__(self):
        super().__init__()
        self.table = None
        if self.table is None:
            table_name = "resources"
            table = db.get_table(table_name)
            print(f"table = {table}")
            if table is None:
                table = create_table(table_name)
            self.table = table

    def check_status(self):
        self._check_has_session()
        try:
            self._session.execute("SELECT 1")
        except db.SQLAlchemyError as e:
            _logger.exception(str(e))
            raise RepositoryStatusError()

    def put(self, resource: Resource):
        self._check_has_session()
        if resource.version is None:
            resource._version = self.get_latest_version(resource.resource_id) + 1
        self._session.execute(
            db.insert(self.table, values=self._resource_to_row(resource))
        )

    update = put

    def resource_ids(self) -> List[str]:
        self._check_has_session()
        query = self._session.query(self.table)
        return [
            row.resource_id for row in query.group_by(self.table.c.resource_id).all()
        ]

    def resources_with_id(self, resource_id: str):
        pass

    def resource_with_id_and_version(
        self, resource_id: str, version: int
    ) -> Optional[Resource]:
        self._check_has_session()
        query = self._session.query(self.table)
        return self._row_to_resource(
            query.filter_by(resource_id=resource_id, version=version).first()
        )

    def get_active_resource(self, resource_id: str) -> Optional[Resource]:
        self._check_has_session()
        query = self._session.query(self.table)
        return self._row_to_resource(
            query.filter_by(resource_id=resource_id, is_published=True).one_or_none()
        )

    def get_latest_version(self, resource_id: str) -> int:
        self._check_has_session()
        row = (
            self._session.query(self.table)
            .order_by(self.table.c.version.desc())
            .filter_by(resource_id=resource_id)
            .first()
        )
        if row is None:
            return 0
        return row.version

    def history_by_resource_id(self, resource_id: str) -> List:
        self._check_has_session()
        query = self._session.query(self.table)
        return [
            self._row_to_resource(row)
            for row in query.filter_by(resource_id=resource_id).all()
        ]

    def get_published_resources(self) -> List[Resource]:
        self._check_has_session()
        subq = (
            self._session.query(
                self.table.c.resource_id,
                db.func.max(self.table.c.last_modified).label("maxdate"),
            )
            .group_by(self.table.c.resource_id)
            .subquery("t2")
        )
        query = self._session.query(self.table).join(
            subq,
            db.and_(
                self.table.c.resource_id == subq.c.resource_id,
                self.table.c.last_modified == subq.c.maxdate,
                self.table.c.is_published == True,
            ),
        )

        return [self._row_to_resource(row) for row in query if row is not None]

    def _resource_to_row(
        self, resource: Resource
    ) -> Tuple[
        None, UUID, str, int, str, Dict, Optional[bool], float, str, str, ResourceOp
    ]:
        return (
            None,
            resource.id,
            resource.resource_id,
            resource.version,
            resource.name,
            resource.config,
            resource.is_published,
            resource.last_modified,
            resource.last_modified_by,
            resource.message,
            resource.op,
        )

    def _row_to_resource(self, row) -> Optional[Resource]:
        return (
            Resource(
                entity_id=row.id,
                resource_id=row.resource_id,
                version=row.version,
                name=row.name,
                config=row.config,
                message=row.message,
                op=row.op,
                is_published=row.is_published,
                last_modified=row.last_modified,
                last_modified_by=row.last_modified_by,
            )
            if row
            else None
        )


def create_table(table_name: str) -> db.Table:
    table = db.Table(
        table_name,
        db.metadata,
        db.Column(
            "history_id",
            db.Integer,
            primary_key=True,
            # autoincrement=True
        ),
        db.Column("id", db.UUIDType, nullable=False),
        db.Column(
            "resource_id",
            db.String(64),
            # primary_key=True,
            nullable=False,
        ),
        db.Column(
            "version",
            db.Integer,
            # primary_key=True,
            # autoincrement=True,
            nullable=False,
        ),
        db.Column(
            "name",
            db.String(64),
            nullable=False,
        ),
        db.Column("config", db.NestedMutableJson, nullable=False),
        db.Column("is_published", db.Boolean, index=True, nullable=True, default=None),
        db.Column("last_modified", db.Float, nullable=False),
        db.Column("last_modified_by", db.String, nullable=False),
        db.Column("message", db.String, nullable=False),
        db.Column("op", db.Enum(ResourceOp), nullable=False),
        db.UniqueConstraint(
            "resource_id", "version", name="resource_version_unique_constraint"
        ),
        # db.UniqueConstraint(
        #     "resource_id", "is_active", name="resource_is_active_unique_constraint"
        # ),
        mysql_character_set="utf8mb4"
        # extend_existing=True
    )
    # db.mapper(
    #     Resource,
    #     table,
    #     properties={
    #         "_id": table.c.id,
    #         "_version": table.c.version,
    #         "_name": table.c.name,
    #         "_resource_id": table.c.resource_id,
    #         # "_is_active": table.c.is_active,
    #     },
    # )

    # @db.event.listens_for(Resource.is_active, "set", retval=True)
    # def update_is_active(target, value, oldvalue, initiator):
    #     if value:
    #         value = True
    #     else:
    #         value = None
    #     return value

    # table.create(db.engine, checkfirst=True)
    return table
