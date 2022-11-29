import dataclasses
import typing
from typing import Dict, Iterable, List, Optional

import injector
from karp.foundation.events import EventBus

from karp.foundation.value_objects import UniqueId
from karp.foundation.commands import CommandBus
from karp.lex import EntryRepositoryUnitOfWorkFactory
from karp.lex.domain import entities as lex_entities
from karp.lex.application import repositories as lex_repositories
from karp.lex.application.queries import (
    ReadOnlyResourceRepository,
    ResourceDto,
)
from karp.tests.foundation.adapters import InMemoryUnitOfWork


@dataclasses.dataclass
class UnitTestContext:
    container: injector.Injector
    command_bus: CommandBus


class InMemoryResourceRepository(lex_repositories.ResourceRepository):
    def __init__(self):
        super().__init__()
        self.resources = {}

    def check_status(self):
        pass

    def _save(self, resource):
        self.resources[resource.id] = resource

    # def _update(self, resource):
    #     r = self._by_id(resource.id)
    #     self.resources.discard(r)
    #     self.resources.add(resource)

    def _by_id(self, id_, *, version=None):
        return self.resources.get(id_)

    def _by_resource_id(self, resource_id):
        return next(
            (res for res in self.resources.values() if res.resource_id == resource_id),
            None,
        )

    def __len__(self):
        return len(self.resources)

    def _get_published_resources(self) -> typing.Iterable[lex_entities.Resource]:
        return (res for res in self.resources.values() if res.is_published)

    def _get_all_resources(self) -> typing.Iterable[lex_entities.Resource]:
        return iter(self.resources.values())

    def resource_ids(self) -> typing.Iterable[str]:
        return (res.resource_id for res in self.resources)

    def num_entities(self) -> int:
        return sum(not res.discarded for res in self.resources.values())


class InMemoryReadResourceRepository(ReadOnlyResourceRepository):
    def __init__(self, resources: Dict):
        self.resources = resources

    def get_by_id(
        self, entity_id: UniqueId, version: Optional[int] = None
    ) -> Optional[ResourceDto]:
        resource = self.resources.get(entity_id)
        if resource:
            return self._row_to_dto(resource)
        return None

    def _get_by_resource_id(self, resource_id: str) -> Optional[ResourceDto]:
        return next(
            (
                self._row_to_dto(res)
                for res in self.resources.values()
                if res.resource_id == resource_id
            ),
            None,
        )

    def _row_to_dto(self, res) -> ResourceDto:
        return ResourceDto(
            entity_id=res.entity_id,
            resource_id=res.resource_id,
            last_modified=res.last_modified,
            last_modified_by=res.last_modified_by,
            version=res.version,
            config=res.config,
            is_published=res.is_published,
            entry_repository_id=res.entry_repository_id,
            name=res.name,
            message=res.message,
            discarded=res.discarded,
        )

    def get_published_resources(self) -> Iterable[ResourceDto]:
        return (
            self._row_to_dto(res) for res in self.resources.values() if res.is_published
        )


class InMemoryEntryRepository(lex_repositories.EntryRepository):
    def __init__(self):
        super().__init__()
        self.entries = set()

    def check_status(self):
        pass

    def _save(self, entry):
        self.entries.add(entry)

    def _update(self, entry):
        r = self._by_id(entry.id)
        self.entries.discard(r)
        self.entries.add(entry)

    def _by_id(
        self,
        id,
        *,
        version=None,
        after_date=None,
        before_date=None,
        oldest_first=False,
    ):
        return next((r for r in self.entries if r.id == id), None)

    # def _by_entry_id(
    #     self,
    #     entry_id,
    #     *,
    #     version=None,
    #     after_date=None,
    #     before_date=None,
    # ):
    #     return next((r for r in self.entries if r.entry_id == entry_id), None)

    def __len__(self):
        return len(self.entries)

    def _create_repository_settings(self, *args):
        pass

    @classmethod
    def from_dict(cls, _):
        return cls()

    def all_entries(self) -> typing.Iterable[lex_entities.Entry]:
        yield from self.entries

    def num_entities(self) -> int:
        return sum(not e.discarded for e in self.entries)

    def by_referenceable(
        self, filters: Optional[Dict] = None, **kwargs
    ) -> list[lex_entities.Entry]:
        return []


class InMemoryEntryUnitOfWork(InMemoryUnitOfWork, lex_repositories.EntryUnitOfWork):
    def __init__(
        self,
        entity_id,
        name: str,
        config: typing.Dict,
        connection_str: typing.Optional[str],
        message: str,
        user: str,
        event_bus: EventBus,
    ):
        InMemoryUnitOfWork.__init__(self)
        lex_repositories.EntryUnitOfWork.__init__(
            self,
            entity_id=entity_id,
            name=name,
            config=config,
            connection_str=connection_str,
            message=message,
            event_bus=event_bus,
        )
        self._entries = InMemoryEntryRepository()
        # self.id = entity_id
        # self.name = name
        # self.config = config

    @property
    def repo(self) -> lex_repositories.EntryRepository:
        return self._entries


class InMemoryEntryUnitOfWork2(InMemoryUnitOfWork, lex_repositories.EntryUnitOfWork):
    def __init__(self, entity_id, name: str, config: typing.Dict):
        InMemoryUnitOfWork.__init__(self)
        lex_repositories.EntryUnitOfWork.__init__(
            self, entity_id=entity_id, name=name, config=config
        )
        self._entries = InMemoryEntryRepository()
        # self.id = entity_id
        # self.name = name
        # self.config = config

    @property
    def repo(self) -> lex_repositories.EntryRepository:
        return self._entries


class InMemoryResourceUnitOfWork(
    InMemoryUnitOfWork, lex_repositories.ResourceUnitOfWork
):
    def __init__(self, event_bus: EventBus):
        InMemoryUnitOfWork.__init__(self)
        lex_repositories.ResourceUnitOfWork.__init__(self, event_bus=event_bus)
        self._resources = InMemoryResourceRepository()

    @property
    def repo(self) -> lex_repositories.ResourceRepository:
        return self._resources


# class InMemoryEntryUowFactory(lex_repositories.EntryUowFactory):
#     def create(
#         self,
#         resource_id: str,
#         resource_config: typing.Dict,
#         entry_repository_settings,
#     ) -> lex_repositories.EntryUnitOfWork:
#         entry_uow = InMemoryEntryUnitOfWork(entry_repository_settings)
#         if "entry_repository_type" in resource_config:
#             entry_uow.repo.type = resource_config["entry_repository_type"]
#         if entry_repository_settings:
#             entry_uow.repo_settings = entry_repository_settings
#         return entry_uow


class InMemoryEntryUnitOfWorkCreator:
    @injector.inject
    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus

    def __call__(
        self,
        entity_id: UniqueId,
        name: str,
        config: Dict,
        connection_str: Optional[str],
        user: str,
        message: str,
        timestamp: float,
    ) -> lex_repositories.EntryUnitOfWork:
        return InMemoryEntryUnitOfWork(
            entity_id=entity_id,
            name=name,
            config=config,
            connection_str=connection_str,
            message=message,
            user=user,
            event_bus=self.event_bus,
        )


def create_entry_uow2(
    entity_id: UniqueId,
    name: str,
    config: Dict,
) -> lex_repositories.EntryUnitOfWork:
    return InMemoryEntryUnitOfWork2(
        entity_id=entity_id,
        name=name,
        config=config,
    )


class InMemoryEntryUowRepository(lex_repositories.EntryUowRepository):
    def __init__(self) -> None:
        super().__init__()
        self._storage: dict[UniqueId, dict] = {}

    def _save(self, entry_repo):
        self._storage[entry_repo.id] = entry_repo

    def _by_id(self, id_, *, version: Optional[int] = None):
        return self._storage.get(id_)

    def __len__(self):
        return len(self._storage)

    def num_entities(self) -> int:
        return sum(not er.discarded for er in self._storage.values())


class InMemoryEntryUowRepositoryUnitOfWork(
    InMemoryUnitOfWork, lex_repositories.EntryUowRepositoryUnitOfWork
):
    def __init__(
        self,
        event_bus: EventBus,
        entry_uow_factory: EntryRepositoryUnitOfWorkFactory,
    ) -> None:
        InMemoryUnitOfWork.__init__(self)
        lex_repositories.EntryUowRepositoryUnitOfWork.__init__(
            self,
            event_bus=event_bus,
            entry_uow_factory=entry_uow_factory,
        )
        self._repo = InMemoryEntryUowRepository()

    @property
    def repo(self) -> lex_repositories.EntryUowRepository:
        return self._repo


class InMemoryLexInfrastructure(injector.Module):
    @injector.provider
    @injector.singleton
    def entry_uow_repo_uow(
        self,
        event_bus: EventBus,
        entry_uow_factory: EntryRepositoryUnitOfWorkFactory,
    ) -> lex_repositories.EntryUowRepositoryUnitOfWork:
        return InMemoryEntryUowRepositoryUnitOfWork(
            event_bus=event_bus,
            entry_uow_factory=entry_uow_factory,
        )

    # @injector.provider
    # def entry_uow_factory(self) -> lex_repositories.EntryRepositoryUnitOfWorkFactory:
    #     return InMemoryEntryRepositoryUnitOfWorkFactory()
    @injector.multiprovider
    def entry_uow_creator_map(
        self,
    ) -> Dict[str, lex_repositories.EntryUnitOfWorkCreator]:
        return {"fake": InMemoryEntryUnitOfWorkCreator}

    @injector.provider
    @injector.singleton
    def resource_uow(self, event_bus: EventBus) -> lex_repositories.ResourceUnitOfWork:
        return InMemoryResourceUnitOfWork(event_bus=event_bus)

    @injector.provider
    @injector.singleton
    def resource_repo(
        self,
        resource_uow: lex_repositories.ResourceUnitOfWork,
    ) -> ReadOnlyResourceRepository:
        return InMemoryReadResourceRepository(
            resources=resource_uow.repo.resources,
        )


# def bootstrap_test_app(
#     resource_uow: lex_repositories.ResourceUnitOfWork = None,
#     entry_uows: lex_repositories.EntriesUnitOfWork = None,
#     entry_uow_factory: lex_repositories.EntryUowFactory = None,
#     search_service_uow: SearchServiceUnitOfWork = None,
#     entry_repo_repo_uow: lex_repositories.EntryRepositoryRepositoryUnitOfWork = None,
# ):
#     return bootstrap_message_bus(
#         resource_uow=resource_uow or InMemoryResourceUnitOfWork(),
#         entry_repo_repo_uow=entry_repo_repo_uow or InMemoryEntryRepositoryRepositoryUnitOfWork(),
#         entry_uows=entry_uows or lex_repositories.EntriesUnitOfWork(),
#         entry_uow_factory=entry_uow_factory or InMemoryEntryUowFactory(),
#         search_service_uow=search_service_uow or InMemorySearchServiceUnitOfWork(),
#         raise_on_all_errors=True
#     )
