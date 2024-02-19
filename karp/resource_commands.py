import logging

from karp.foundation.timings import utc_now
from karp.foundation.value_objects import make_unique_id
from karp.lex.domain import entities
from karp.lex.domain.dtos import ResourceDto
from karp.lex.domain.errors import IntegrityError, ResourceNotFound
from karp.lex.infrastructure import ResourceRepository
from karp.search_infrastructure.repositories.es6_indicies import Es6Index

logger = logging.getLogger(__name__)


class ResourceCommands:
    def __init__(self, session, resources, index):
        self.session = session
        self.resources: ResourceRepository = resources
        self.index: Es6Index = index

    def create_resource(self, resource_id, name, config, user):
        existing_resource = self.resources.by_resource_id_optional(resource_id)
        if existing_resource and not existing_resource.discarded:
            raise IntegrityError(f"Resource with resource_id='{resource_id}' already exists.")

        resource = entities.create_resource(
            resource_id=resource_id,
            config=config,
            message=f"Resource '{resource_id}' created.",
            table_name=f"{resource_id}_{make_unique_id()}",
            created_at=utc_now(),
            created_by=user,
            name=name,
        )

        self.resources.save(resource)
        self.session.commit()
        self._create_search_servie_handler(resource)
        return ResourceDto(**resource.serialize())

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
        self._resource_published_handler(resource_id)

    def delete_resource(self, resource_id, user, message):
        logger.info("deleting resource", extra={"resource_id": resource_id})
        resource = self.resources.by_resource_id(resource_id)
        resource.discard(user=user, message=message, timestamp=utc_now())
        self.resources.save(resource)
        self.session.commit()
        self._deleting_index(resource_id)

    def _deleting_index(self, resource_id):
        self.index.delete_index(resource_id)

    def _create_search_servie_handler(self, resource):
        self.index.create_index(resource.resource_id, resource.config)

    def _resource_published_handler(self, resource_id):
        self.index.publish_index(resource_id)
