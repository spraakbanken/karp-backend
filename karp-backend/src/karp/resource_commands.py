import logging

from karp.lex import ResourceUnitOfWork
from karp.lex.application.dtos import ResourceDto
from karp.lex.domain import entities
from karp.lex.domain.errors import IntegrityError, ResourceNotFound
from karp.lex_core.value_objects import make_unique_id
from karp.search import IndexUnitOfWork
from karp.timings import utc_now

logger = logging.getLogger(__name__)


class ResourceCommands:
    def __init__(self, resource_uow, index_uow):
        self.resource_uow: ResourceUnitOfWork = resource_uow
        self.index_uow: IndexUnitOfWork = index_uow

    def create_resource(self, resource_id, name, config, user):
        with self.resource_uow as uow:
            existing_resource = uow.repo.get_by_resource_id_optional(resource_id)
            if existing_resource and not existing_resource.discarded:
                raise IntegrityError(
                    f"Resource with resource_id='{resource_id}' already exists."
                )

            resource = entities.create_resource(
                resource_id=resource_id,
                config=config,
                message=f"Resource '{resource_id}' created.",
                table_name=f"{resource_id}_{make_unique_id()}",
                created_at=utc_now(),
                created_by=user,
                name=name,
            )

            uow.repo.save(resource)
            uow.commit()
            self._create_search_servie_handler(resource)
        return ResourceDto(**resource.serialize())

    def update_resource(self, resource_id, name, version, config, message, user):
        with self.resource_uow as uow:
            resource = uow.repo.by_resource_id(resource_id)
            updated = resource.update(
                name=name,
                config=config,
                user=user,
                message=message,
                timestamp=utc_now(),
                version=version,
            )
            if updated:
                uow.repo.save(resource)
            uow.commit()

    def publish_resource(self, resource_id, message, user, version):
        logger.info("publishing resource", extra={"resource_id": resource_id})
        with self.resource_uow as uow:
            resource = uow.repo.by_resource_id(resource_id)
            if not resource:
                raise ResourceNotFound(resource_id)
            resource.publish(
                user=user,
                message=message,
                timestamp=utc_now(),
                version=version,
            )
            uow.repo.save(resource)
            uow.commit()
            self._resource_published_handler(resource_id)

    def delete_resource(self, resource_id, user, message):
        logger.info("deleting resource", extra={"resource_id": resource_id})
        with self.resource_uow as uow:
            resource = uow.repo.by_resource_id(resource_id)
            resource.discard(user=user, message=message, timestamp=utc_now())
            uow.repo.save(resource)
            uow.commit()
            self._deleting_index(resource_id)

    def _deleting_index(self, resource_id):
        with self.index_uow as uw:
            uw.repo.delete_index(resource_id)
            uw.commit()

    def _create_search_servie_handler(self, resource):
        with self.index_uow as uw:
            uw.repo.create_index(resource.resource_id, resource.config)
            uw.commit()

    def _resource_published_handler(self, resource_id):
        with self.index_uow as uw:
            uw.repo.publish_index(resource_id)
            uw.commit()
