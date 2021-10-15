import abc
import typing
from typing import Dict, List, Optional, Tuple

from karp.foundation import repository
from karp.lex.domain import entities, errors
from karp.lex.domain.value_objects import UniqueId


class EntryRepository(repository.Repository[entities.Entry]):
    EntityNotFound = errors.EntryNotFound

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, settings: Dict):
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def _create_repository_settings(
        cls, resource_id: str, resource_config: typing.Dict
    ):
        raise NotImplementedError()

    def __init__(self):
        super().__init__()
        self.settings = {}

    def by_id(
        self,
        id_: UniqueId,
        *,
        version: Optional[int] = None,
        after_date: Optional[float] = None,
        before_date: Optional[float] = None,
        oldest_first: bool = False,
    ) -> entities.Entry:
        entry = self._by_id(
            id_,
            version=version,
            after_date=after_date,
            before_date=before_date,
            oldest_first=oldest_first,
        )
        if entry:
            self.seen.add(entry)
            return entry
        raise errors.EntryNotFound(id_=id_)

    @abc.abstractmethod
    def _by_id(
        self,
        id: UniqueId,
        *,
        version: Optional[int] = None,
        after_date: Optional[float] = None,
        before_date: Optional[float] = None,
        oldest_first: bool = False,
    ) -> typing.Optional[entities.Entry]:
        raise NotImplementedError()

    # @abc.abstractmethod
    def move(self, entry: entities.Entry, *, old_entry_id: str):
        raise NotImplementedError()

    # @abc.abstractmethod
    def delete(self, entry: entities.Entry):
        raise NotImplementedError()

    # @abc.abstractmethod
    def entry_ids(self) -> List[str]:
        raise NotImplementedError()

    def by_entry_id(
        self, entry_id: str, *, version: Optional[int] = None
    ) -> entities.Entry:
        entry = self._by_entry_id(entry_id, version=version)
        if entry:
            self.seen.add(entry)
            return entry
        raise errors.EntryNotFound(
            f'Entry with entry_id="{entry_id}"',
            entity_id=None,
        )

    @abc.abstractmethod
    def _by_entry_id(
        self, entry_id: str, *, version: Optional[int] = None
    ) -> Optional[entities.Entry]:
        raise NotImplementedError()

    # @abc.abstractmethod
    def teardown(self):
        """Use for testing purpose."""
        return

    # @abc.abstractmethod
    # def by_referenceable(self, filters: Optional[Dict] = None, **kwargs) -> List[Entry]:
    #     raise NotImplementedError()

    # @abc.abstractmethod
    def get_history(
        self,
        user_id: Optional[str] = None,
        entry_id: Optional[str] = None,
        from_date: Optional[float] = None,
        to_date: Optional[float] = None,
        from_version: Optional[int] = None,
        to_version: Optional[int] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Tuple[List[entities.Entry], int]:
        return [], 0

    @abc.abstractmethod
    def all_entries(self) -> typing.Iterable[entities.Entry]:
        """Return all entries."""
        return []
