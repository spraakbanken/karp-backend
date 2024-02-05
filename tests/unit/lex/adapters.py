import copy
import dataclasses
import typing
from typing import Dict, Iterable, Optional, Tuple

import injector
from karp.foundation.repository import Repository
from karp.lex.application import repositories as lex_repositories
from karp.lex.application.dtos import ResourceDto
from karp.lex.application.repositories import (
    EntryUnitOfWork,
)
from karp.lex.domain import entities as lex_entities
from karp.lex_core.value_objects import UniqueId, UniqueIdType, unique_id
from karp.lex_core.value_objects.unique_id import UniqueIdPrimitive
from karp.lex.domain import errors
from karp.lex_infrastructure import SqlReadOnlyResourceRepository, SqlResourceUnitOfWork
from tests.foundation.adapters import InMemoryUnitOfWork


@dataclasses.dataclass
class UnitTestContext:
    container: injector.Injector


def ensure_correct_id_type(v) -> unique_id.UniqueId:
    try:
        return unique_id.UniqueId.validate(v)
    except ValueError as exc:
        raise ValueError(f"expected valid UniqueId, got '{v}' (type: `{type(v)}')") from exc


class InMemoryResourceRepository(lex_repositories.ResourceRepository):
    def __init__(self):  # noqa: ANN204
        super().__init__()
        self.resources = {}

    def _save(self, resource: lex_entities.Resource) -> None:
        resource_id = ensure_correct_id_type(resource.id)
        self.resources[resource_id] = resource

    def _by_id(self, id_, *, version=None):  # noqa: ANN202
        if resource := self.resources.get(id_):
            return copy.deepcopy(resource)
        return None

    def _by_resource_id(self, resource_id):  # noqa: ANN202
        return next(
            (res for res in self.resources.values() if res.resource_id == resource_id),
            None,
        )

    def __len__(self):  # noqa: ANN204
        return len(self.resources)

    def _get_published_resources(self) -> typing.Iterable[lex_entities.Resource]:
        return (res for res in self.resources.values() if res.is_published)

    def _get_all_resources(self) -> typing.Iterable[lex_entities.Resource]:
        return iter(self.resources.values())

    def resource_ids(self) -> typing.Iterable[str]:
        return (res.resource_id for res in self.resources)


class InMemoryReadResourceRepository(SqlReadOnlyResourceRepository):
    def __init__(self, resources: Dict):  # noqa: ANN204
        self.resources = resources

    def get_by_id(
        self,
        id: UniqueIdPrimitive,
        version: Optional[int] = None,  # noqa: A002
    ) -> Optional[ResourceDto]:
        resource_id = UniqueId.validate(id)
        if resource := self.resources.get(resource_id):
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

    def _row_to_dto(self, res: lex_entities.Resource) -> ResourceDto:
        return ResourceDto(**res.serialize())

    def get_published_resources(self) -> Iterable[ResourceDto]:
        return (self._row_to_dto(res) for res in self.resources.values() if res.is_published)


class InMemoryEntryRepository(Repository):
    def __init__(self):  # noqa: ANN204
        super().__init__()
        self.entries = {}

    def check_status(self):  # noqa: ANN201
        pass

    def _save(self, entry):  # noqa: ANN202
        entry_id = ensure_correct_id_type(entry.id)
        self.entries[entry_id] = copy.deepcopy(entry)

    def by_id(  # noqa: D102
        self,
        id_: UniqueId,
        *,
        version: Optional[int] = None,
        after_date: Optional[float] = None,
        before_date: Optional[float] = None,
        oldest_first: bool = False,
        **kwargs,  # noqa: ANN003
    ):
        if entry := self._by_id(
            id_,
            version=version,
            after_date=after_date,
            before_date=before_date,
            oldest_first=oldest_first,
        ):
            return entry
        raise errors.EntryNotFound(id_=id_)

    def _by_id(  # noqa: ANN202
        self,
        id,  # noqa: A002
        *,
        version=None,
        after_date=None,
        before_date=None,
        oldest_first=False,
    ):
        entry_id = ensure_correct_id_type(id)
        if entry := self.entries.get(entry_id):
            return copy.deepcopy(entry)
        print(f"{self.entries=}")
        return None

    def __len__(self):  # noqa: ANN204
        return len(self.entries)

    @classmethod
    def from_dict(cls, _):  # noqa: ANN206
        return cls()

    def all_entries(self) -> typing.Iterable[lex_entities.Entry]:
        yield from self.entries.values()


class InMemoryEntryUnitOfWork(InMemoryUnitOfWork, lex_repositories.EntryUnitOfWork):
    def __init__(  # noqa: ANN204
        self,
        id: UniqueId,  # noqa: A002
        name: str,
        config: typing.Dict,
        message: str,
        user: str,
    ):
        InMemoryUnitOfWork.__init__(self)
        lex_repositories.EntryUnitOfWork.__init__(
            self,
            id=id,
            name=name,
            config=config,
            message=message,
        )
        self._entries = InMemoryEntryRepository()
        # self.id = entity_id
        # self.name = name
        # self.config = config

    @property
    def repo(self):
        return self._entries


class InMemoryResourceUnitOfWork(InMemoryUnitOfWork, SqlResourceUnitOfWork):
    def __init__(self):  # noqa: ANN204
        InMemoryUnitOfWork.__init__(self)
        SqlResourceUnitOfWork.__init__(self)
        self._resources = InMemoryResourceRepository()

    @property
    def repo(self) -> lex_repositories.ResourceRepository:
        return self._resources

    def resource_to_entry_uow(self, resource: lex_entities.Resource) -> EntryUnitOfWork:
        return self._storage.get(resource.table_name)


class InMemoryLexInfrastructure(injector.Module):
    @injector.provider
    @injector.singleton
    def resource_uow(self) -> SqlResourceUnitOfWork:
        return InMemoryResourceUnitOfWork()

    @injector.provider
    @injector.singleton
    def resource_repo(
        self,
        resource_uow: SqlResourceUnitOfWork,
    ) -> SqlReadOnlyResourceRepository:
        return InMemoryReadResourceRepository(
            resources=resource_uow.repo.resources,  # type: ignore
        )
