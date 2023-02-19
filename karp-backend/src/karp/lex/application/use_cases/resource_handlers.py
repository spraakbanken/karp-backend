import logging  # noqa: D100, I001
import typing


from karp.lex.domain import errors, entities
from karp.foundation import events as foundation_events
from karp.command_bus import CommandHandler
from karp.lex.application.queries import ResourceDto
from karp.lex.application import repositories as lex_repositories
from karp.lex import commands
from karp.lex.application import repositories


logger = logging.getLogger(__name__)

# resource_models = {}  # Dict
# history_models = {}  # Dict
# resource_configs = {}  # Dict
# resource_versions = {}  # Dict[str, int]
# field_translations = {}  # Dict[str, Dict[str, List[str]]]


class BasingResource:  # noqa: D101
    def __init__(self, resource_uow: repositories.ResourceUnitOfWork) -> None:  # noqa: D107
        self.resource_uow = resource_uow

    def collect_new_events(self) -> typing.Iterable[foundation_events.Event]:  # noqa: D102
        yield from self.resource_uow.collect_new_events()


class CreatingResource(CommandHandler[commands.CreateResource], BasingResource):  # noqa: D101
    def __init__(  # noqa: D107
        self,
        resource_uow: repositories.ResourceUnitOfWork,
        entry_repo_uow: lex_repositories.EntryUowRepositoryUnitOfWork,
    ) -> None:
        super().__init__(resource_uow=resource_uow)
        self.entry_repo_uow = entry_repo_uow

    def execute(self, command: commands.CreateResource) -> ResourceDto:  # noqa: D102
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
                and existing_resource.id != command.id
            ):
                raise errors.IntegrityError(
                    f"Resource with resource_id='{command.resource_id}' already exists."
                )

            resource, events = entities.create_resource(
                entity_id=command.id,
                resource_id=command.resource_id,
                config=command.config,
                message=command.message,
                entry_repo_id=command.entry_repo_id,
                created_at=command.timestamp,
                created_by=command.user,
                name=command.name,
            )

            uow.repo.save(resource)
            uow.post_on_commit(events)
            uow.commit()
        return ResourceDto(**resource.dict())

    def collect_new_events(self) -> typing.Iterable[foundation_events.Event]:  # noqa: D102
        yield from self.resource_uow.collect_new_events()


class SettingEntryRepoId(CommandHandler[commands.SetEntryRepoId], BasingResource):  # noqa: D101
    def __init__(  # noqa: D107
        self,
        resource_uow: repositories.ResourceUnitOfWork,
        entry_repo_uow: lex_repositories.EntryUowRepositoryUnitOfWork,
    ) -> None:
        super().__init__(resource_uow=resource_uow)
        self.entry_repo_uow = entry_repo_uow

    def execute(self, command: commands.SetEntryRepoId) -> None:  # noqa: D102
        with self.entry_repo_uow as uow:
            entry_repo_exists = uow.repo.get_by_id_optional(command.entry_repo_id)
            if not entry_repo_exists:
                raise errors.NoSuchEntryRepository(
                    f"Entry repository '{command.entry_repo_id}' not found"
                )

        with self.resource_uow as uow:
            resource = uow.repo.get_by_resource_id(command.resource_id)

            events = resource.set_entry_repo_id(
                entry_repo_id=command.entry_repo_id,
                user=command.user,
                timestamp=command.timestamp,
            )

            uow.repo.save(resource)
            uow.post_on_commit(events)
            uow.commit()


class UpdatingResource(CommandHandler[commands.UpdateResource], BasingResource):  # noqa: D101
    def __init__(self, resource_uow: repositories.ResourceUnitOfWork) -> None:  # noqa: D107
        super().__init__(resource_uow=resource_uow)

    def execute(self, command: commands.UpdateResource):  # noqa: ANN201, D102
        with self.resource_uow as uow:
            resource = uow.repo.by_resource_id(command.resource_id)
            events = resource.update(
                name=command.name,
                config=command.config,
                user=command.user,
                message=command.message,
                timestamp=command.timestamp,
                version=command.version,
            )
            if events:
                uow.repo.save(resource)
            uow.post_on_commit(events)
            uow.commit()

    def collect_new_events(self) -> typing.Iterable[foundation_events.Event]:  # noqa: D102
        yield from self.resource_uow.collect_new_events()


class PublishingResource(CommandHandler[commands.PublishResource], BasingResource):  # noqa: D101
    def __init__(  # noqa: D107
        self,
        resource_uow: repositories.ResourceUnitOfWork,
        **kwargs,  # noqa: ANN003
    ) -> None:
        super().__init__(resource_uow=resource_uow)

    def execute(self, command: commands.PublishResource):  # noqa: ANN201, D102
        logger.info("publishing resource", extra={"resource_id": command.resource_id})
        with self.resource_uow as uow:
            resource = uow.repo.by_resource_id(command.resource_id)
            if not resource:
                raise errors.ResourceNotFound(command.resource_id)
            events = resource.publish(
                user=command.user,
                message=command.message,
                timestamp=command.timestamp,
                version=command.version,
            )
            uow.repo.save(resource)
            uow.post_on_commit(events)
            uow.commit()

    def collect_new_events(self) -> typing.Iterable[foundation_events.Event]:  # noqa: D102
        yield from self.resource_uow.collect_new_events()


class DeletingResource(CommandHandler[commands.DeleteResource], BasingResource):  # noqa: D101
    def __init__(  # noqa: D107
        self,
        resource_uow: repositories.ResourceUnitOfWork,
        **kwargs,  # noqa: ANN003
    ) -> None:
        super().__init__(resource_uow=resource_uow)

    def execute(self, command: commands.DeleteResource):  # noqa: ANN201, D102
        logger.info("deleting resource", extra={"resource_id": command.resource_id})
        with self.resource_uow as uow:
            resource = uow.repo.by_resource_id(command.resource_id)
            if not resource:
                raise errors.ResourceNotFound(command.resource_id)
            events = resource.discard(
                user=command.user, message=command.message, timestamp=command.timestamp
            )
            uow.repo.save(resource)
            uow.post_on_commit(events)
            uow.commit()

    def collect_new_events(self) -> typing.Iterable[foundation_events.Event]:  # noqa: D102
        yield from self.resource_uow.collect_new_events()
