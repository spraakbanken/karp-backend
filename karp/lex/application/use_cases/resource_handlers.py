import json
import logging
import typing
from pathlib import Path
from typing import IO, Dict, Generic, List, Optional, Tuple

import logging

from karp.lex.domain import errors, entities
from karp.lex.domain.entities import Resource
from karp.foundation import events as foundation_events
from karp.foundation.commands import CommandHandler
from karp.lex.application.queries import ResourceDto
from karp.lex.application import repositories as lex_repositories
from karp.lex.domain import commands
from karp.lex.application import repositories


logger = logging.getLogger(__name__)

# resource_models = {}  # Dict
# history_models = {}  # Dict
# resource_configs = {}  # Dict
# resource_versions = {}  # Dict[str, int]
# field_translations = {}  # Dict[str, Dict[str, List[str]]]


class BasingResource:
    def __init__(self, resource_uow: repositories.ResourceUnitOfWork) -> None:
        self.resource_uow = resource_uow

    def collect_new_events(self) -> typing.Iterable[foundation_events.Event]:
        yield from self.resource_uow.collect_new_events()


class CreatingResource(CommandHandler[commands.CreateResource], BasingResource):
    def __init__(
        self,
        resource_uow: repositories.ResourceUnitOfWork,
        entry_repo_uow: lex_repositories.EntryUowRepositoryUnitOfWork,
    ) -> None:
        super().__init__(resource_uow=resource_uow)
        self.entry_repo_uow = entry_repo_uow

    def execute(self, command: commands.CreateResource) -> ResourceDto:
        with self.entry_repo_uow as uow:
            entry_repo_exists = uow.repo.get_by_id_optional(command.entry_repo_id)
            if not entry_repo_exists:
                raise errors.NoSuchEntryRepository(
                    f"Entry repository '{command.entry_repo_id}' not found"
                )

        with self.resource_uow as uow:
            existing_resource = uow.repo.get_by_resource_id_optional(
                command.resource_id
            )
            if (
                existing_resource
                and not existing_resource.discarded
                and existing_resource.entity_id != command.entity_id
            ):
                raise errors.IntegrityError(
                    f"Resource with resource_id='{command.resource_id}' already exists."
                )

            resource = entities.create_resource(
                entity_id=command.entity_id,
                resource_id=command.resource_id,
                config=command.config,
                message=command.message,
                entry_repo_id=command.entry_repo_id,
                created_at=command.timestamp,
                created_by=command.user,
                name=command.name,
            )

            uow.repo.save(resource)
            uow.commit()
        return ResourceDto(**resource.dict())

    def collect_new_events(self) -> typing.Iterable[foundation_events.Event]:
        yield from self.resource_uow.collect_new_events()


class SettingEntryRepoId(CommandHandler[commands.SetEntryRepoId], BasingResource):
    def __init__(
        self,
        resource_uow: repositories.ResourceUnitOfWork,
        entry_repo_uow: lex_repositories.EntryUowRepositoryUnitOfWork,
    ) -> None:
        super().__init__(resource_uow=resource_uow)
        self.entry_repo_uow = entry_repo_uow

    def execute(self, command: commands.SetEntryRepoId) -> None:
        with self.entry_repo_uow as uow:
            entry_repo_exists = uow.repo.get_by_id_optional(command.entry_repo_id)
            if not entry_repo_exists:
                raise errors.NoSuchEntryRepository(
                    f"Entry repository '{command.entry_repo_id}' not found"
                )

        with self.resource_uow as uow:
            resource = uow.repo.get_by_resource_id(command.resource_id)

            resource.set_entry_repo_id(
                entry_repo_id=command.entry_repo_id,
                user=command.user,
                timestamp=command.timestamp,
            )

            uow.repo.save(resource)
            uow.commit()


class UpdatingResource(CommandHandler[commands.UpdateResource], BasingResource):
    def __init__(self, resource_uow: repositories.ResourceUnitOfWork) -> None:
        super().__init__(resource_uow=resource_uow)

    def execute(self, command: commands.UpdateResource):
        with self.resource_uow as uow:
            resource = uow.repo.by_resource_id(command.resource_id)
            if resource.update(
                name=command.name,
                config=command.config,
                user=command.user,
                message=command.message,
                timestamp=command.timestamp,
                version=command.version,
            ):

                uow.repo.save(resource)
            uow.commit()

    def collect_new_events(self) -> typing.Iterable[foundation_events.Event]:
        yield from self.resource_uow.collect_new_events()


class PublishingResource(CommandHandler[commands.PublishResource], BasingResource):
    def __init__(
        self,
        resource_uow: repositories.ResourceUnitOfWork,
        **kwargs,
    ) -> None:
        super().__init__(resource_uow=resource_uow)

    def execute(self, command: commands.PublishResource):
        logger.info("publishing resource", extra={"resource_id": command.resource_id})
        with self.resource_uow as uow:
            resource = uow.repo.by_resource_id(command.resource_id)
            if not resource:
                raise errors.ResourceNotFound(command.resource_id)
            resource.publish(
                user=command.user,
                message=command.message,
                timestamp=command.timestamp,
                version=command.version,
            )
            uow.repo.save(resource)
            uow.commit()

    def collect_new_events(self) -> typing.Iterable[foundation_events.Event]:
        yield from self.resource_uow.collect_new_events()


class DeletingResource(CommandHandler[commands.DeleteResource], BasingResource):
    def __init__(
        self,
        resource_uow: repositories.ResourceUnitOfWork,
        **kwargs,
    ) -> None:
        super().__init__(resource_uow=resource_uow)

    def execute(self, command: commands.DeleteResource):
        logger.info("deleting resource", extra={"resource_id": command.resource_id})
        with self.resource_uow as uow:
            resource = uow.repo.by_resource_id(command.resource_id)
            if not resource:
                raise errors.ResourceNotFound(command.resource_id)
            resource.discard(
                user=command.user, message=command.message, timestamp=command.timestamp
            )
            uow.repo.save(resource)
            uow.commit()

    def collect_new_events(self) -> typing.Iterable[foundation_events.Event]:
        yield from self.resource_uow.collect_new_events()
