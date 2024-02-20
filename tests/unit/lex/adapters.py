import copy
import dataclasses
import typing
from typing import Optional

import injector

from karp.lex.domain import entities as lex_entities
from karp.foundation.value_objects import UniqueId, unique_id
from karp.lex.infrastructure import ResourceRepository, EntryRepository
from karp.lex.domain import errors


@dataclasses.dataclass
class UnitTestContext:
    container: injector.Injector


def ensure_correct_id_type(v) -> unique_id.UniqueId:
    try:
        return unique_id.UniqueId.validate(v)
    except ValueError as exc:
        raise ValueError(f"expected valid UniqueId, got '{v}' (type: `{type(v)}')") from exc


class InMemoryResourceRepository(ResourceRepository):
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

    def get_published_resources(self) -> typing.Iterable[lex_entities.Resource]:
        return (res for res in self.resources.values() if res.is_published)

    def get_all_resources(self) -> typing.Iterable[lex_entities.Resource]:
        return iter(self.resources.values())

    def resource_ids(self) -> typing.Iterable[str]:
        return (res.resource_id for res in self.resources)


class InMemoryEntryRepository(EntryRepository):
    def __init__(self):
        self.entries = {}

    def check_status(self):
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


class InMemoryLexInfrastructure(injector.Module):
    @injector.provider
    @injector.singleton
    def resources(self) -> ResourceRepository:
        return InMemoryResourceRepository()
