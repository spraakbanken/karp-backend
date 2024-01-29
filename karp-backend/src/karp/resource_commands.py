import logging

from karp.lex import EntryUowRepositoryUnitOfWork, ResourceUnitOfWork
from karp.lex.application.dtos import ResourceDto
from karp.lex.domain import entities
from karp.lex.domain.errors import IntegrityError, NoSuchEntryRepository, ResourceNotFound
from karp.lex_core.value_objects import make_unique_id
from karp.timings import utc_now

logger = logging.getLogger(__name__)


class ResourceCommands:
    def __init__(self, entry_repo_uow, resource_uow):
        self.entry_repo_uow: EntryUowRepositoryUnitOfWork = entry_repo_uow
        self.resource_uow: ResourceUnitOfWork = resource_uow

    def create_resource(self, resource_id, name, config, user, entry_repo_id):
        with self.entry_repo_uow as uow:
            entry_repo_exists = uow.repo.get_by_id_optional(entry_repo_id)
            if not entry_repo_exists:
                raise NoSuchEntryRepository(f"Entry repository '{entry_repo_id}' not found")

        with self.resource_uow as uow:
            existing_resource = uow.repo.get_by_resource_id_optional(resource_id)
            if existing_resource and not existing_resource.discarded:
                raise IntegrityError(
                    f"Resource with resource_id='{resource_id}' already exists."
                )

            resource, events = entities.create_resource(
                resource_id=resource_id,
                config=config,
                message=f"Resource '{resource_id}' created.",
                entry_repo_id=entry_repo_id,
                created_at=utc_now(),
                created_by=user,
                name=name,
            )

            uow.repo.save(resource)
            uow.post_on_commit(events)
            uow.commit()
        return ResourceDto(**resource.serialize())

    def set_entry_repo_id(self, resource_id, entry_repo_id, user):
        with self.entry_repo_uow as uow:
            entry_repo_exists = uow.repo.get_by_id_optional(entry_repo_id)
            if not entry_repo_exists:
                raise NoSuchEntryRepository(f"Entry repository '{entry_repo_id}' not found")

        with self.resource_uow as uow:
            resource = uow.repo.get_by_resource_id(resource_id)

            events = resource.set_entry_repo_id(
                entry_repo_id=entry_repo_id,
                user=user,
                timestamp=utc_now(),
            )

            uow.repo.save(resource)
            uow.post_on_commit(events)
            uow.commit()

    def update_resource(self, resource_id, name, version, config, message, user):
        with self.resource_uow as uow:
            resource = uow.repo.by_resource_id(resource_id)
            events = resource.update(
                name=name,
                config=config,
                user=user,
                message=message,
                timestamp=utc_now(),
                version=version,
            )
            if events:
                uow.repo.save(resource)
            uow.post_on_commit(events)
            uow.commit()

    def publish_resource(self, resource_id, message, user, version):
        logger.info("publishing resource", extra={"resource_id": resource_id})
        with self.resource_uow as uow:
            resource = uow.repo.by_resource_id(resource_id)
            if not resource:
                raise ResourceNotFound(resource_id)
            events = resource.publish(
                user=user,
                message=message,
                timestamp=utc_now(),
                version=version,
            )
            uow.repo.save(resource)
            uow.post_on_commit(events)
            uow.commit()

    def delete_resource(self, resource_id, user, message):
        logger.info("deleting resource", extra={"resource_id": resource_id})
        with self.resource_uow as uow:
            resource = uow.repo.by_resource_id(resource_id)
            if not resource:
                raise ResourceNotFound(resource_id)

            # sends a ResourceDiscarded-event, which via the deleting_index method in the injector.multiprovider
            #  is instantiated to a DeletingIndex-event with a IndexUnitOfWork attribute (magically instantiated by the provider).
            # The DeletingIndex event calls delete_index on the IndexUnitOfWork, which deletes the elastic search index of the given resource and also
            # deletes its corresponding row from the elastic search config.
            events = resource.discard(user=user, message=message, timestamp=utc_now())
            uow.repo.save(resource)
            uow.post_on_commit(events)
            uow.commit()

        with self.entry_repo_uow as uow:
            entry_repo = uow.repo.get_by_id(resource.entry_repository_id)
            events = entry_repo.discard(user=user, timestamp=utc_now())
            uow.repo.save(entry_repo)
            uow.post_on_commit(events)
            uow.commit()


    def create_entry_repository(self, name, config, user, message, connection_str=None):

        entry_repo, events = self.entry_repo_uow.create(
            id=make_unique_id(),
            name=name,
            config=config,
            connection_str=connection_str,
            user=user,
            timestamp=utc_now(),
            message=message,
        )

        logger.debug("Created entry repo", extra={"entry_repo": entry_repo})
        with self.entry_repo_uow as uow:
            logger.debug("Saving...")
            uow.repo.save(entry_repo)
            uow.post_on_commit(events)
            uow.commit()
        return entry_repo
