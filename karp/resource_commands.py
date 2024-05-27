import logging

from injector import inject
from sqlalchemy.orm import Session

from karp import plugins
from karp.foundation.timings import utc_now
from karp.lex.domain import entities
from karp.lex.domain.dtos import ResourceDto
from karp.lex.domain.errors import IntegrityError, ResourceNotFound
from karp.lex.infrastructure import ResourceRepository
from karp.plugins import Plugins
from karp.search.infrastructure.es.indices import EsIndex

logger = logging.getLogger(__name__)


class ResourceCommands:
    @inject
    def __init__(
        self, session: Session, resources: ResourceRepository, index: EsIndex, plugins: Plugins
    ):
        self.session: Session = session
        self.resources: ResourceRepository = resources
        self.index: EsIndex = index
        self.plugins: Plugins = plugins

    def create_resource(self, resource_id, name, config, user):
        existing_resource = self.resources.by_resource_id_optional(resource_id)
        if existing_resource and not existing_resource.discarded:
            raise IntegrityError(f"Resource with resource_id='{resource_id}' already exists.")

        resource = entities.create_resource(
            resource_id=resource_id,
            config=config,
            message=f"Resource '{resource_id}' created.",
            created_at=utc_now(),
            created_by=user,
            name=name,
        )

        self.resources.save(resource)
        config = plugins.transform_config(self.plugins, resource.config)
        self.index.create_index(resource.resource_id, config)
        self.session.commit()
        return ResourceDto.from_resource(resource)

    def update_resource(self, resource_id, name, version, config, message, user):
        resource = self.resources.by_resource_id(resource_id)
        updated = resource.update(
            name=name,
            config=config,
            user=user,
            message=message,
            timestamp=utc_now(),
            version=version,
        )
        if updated:
            self.resources.save(resource)
        self.session.commit()

    def publish_resource(self, resource_id, message, user, version):
        logger.info("publishing resource", extra={"resource_id": resource_id})
        resource = self.resources.by_resource_id(resource_id)
        if not resource:
            raise ResourceNotFound(resource_id)
        resource.publish(
            user=user,
            message=message,
            timestamp=utc_now(),
            version=version,
        )
        self.resources.save(resource)
        self.session.commit()

    def unpublish_resource(self, resource_id, user, version, keep_index=False):
        logger.info("unpublishing resource", extra={"resource_id": resource_id})
        resource = self.resources.by_resource_id(resource_id)
        if not resource.is_published:
            return False
        resource.unpublish(user=user, version=version)
        self.resources.save(resource)
        self.session.commit()
        if not keep_index:
            self.index.delete_index(resource_id)
        return True

    def delete_resource(self, resource_id):
        resource = self.resources.by_resource_id(resource_id)
        if not resource:
            return False

        # delete the index with alias "resource_id" from Elasticsearch
        self.index.delete_index(resource_id)

        # drop resource table
        resource = self.resources.by_resource_id(resource_id)
        self.resources.remove_resource_table(resource)

        # delete all rows from resource table associated with resource_id
        self.resources.delete_all_versions(resource_id)
        self.session.commit()
        return True
