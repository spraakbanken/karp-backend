import abc  # noqa: D100
import typing
from typing import Dict, List, Optional, Tuple

from karp.foundation import entity, events, repository, unit_of_work
from karp.lex.domain import entities, errors
from karp.lex_core.value_objects import UniqueId


class EntryRepository(repository.Repository[entities.Entry]):  # noqa: D101
    EntityNotFound = errors.EntryNotFound

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, settings: Dict):  # noqa: ANN206, D102
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def _create_repository_settings(  # noqa: ANN206
        cls, resource_id: str, resource_config: typing.Dict
    ):
        raise NotImplementedError()

    def __init__(self):  # noqa: D107, ANN204
        super().__init__()
        self.settings = {}

    def by_id(  # noqa: D102
        self,
        id_: UniqueId,
        *,
        version: Optional[int] = None,
        after_date: Optional[float] = None,
        before_date: Optional[float] = None,
        oldest_first: bool = False,
        **kwargs,  # noqa: ANN003
    ) -> entities.Entry:
        if entry := self._by_id(
            id_,
            version=version,
            after_date=after_date,
            before_date=before_date,
            oldest_first=oldest_first,
        ):
            return entry
        raise errors.EntryNotFound(id_=id_)

    @abc.abstractmethod
    def _by_id(
        self,
        id: UniqueId,  # noqa: A002
        *,
        version: Optional[int] = None,
        after_date: Optional[float] = None,
        before_date: Optional[float] = None,
        oldest_first: bool = False,
        **kwargs,  # noqa: ANN003
    ) -> typing.Optional[entities.Entry]:
        raise NotImplementedError()

    def entity_ids(self) -> List[str]:  # noqa: D102
        raise NotImplementedError()

    # @abc.abstractmethod
    def teardown(self):  # noqa: ANN201
        """Use for testing purpose."""
        return

    @abc.abstractmethod
    def by_referenceable(  # noqa: D102
        self, filters: Optional[Dict] = None, **kwargs  # noqa: ANN003
    ) -> list[entities.Entry]:
        raise NotImplementedError()

    # @abc.abstractmethod
    def get_history(  # noqa: D102
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


class EntryUnitOfWork(  # noqa: D101
    entity.TimestampedEntity,
    unit_of_work.UnitOfWork[EntryRepository],
):
    repository_type: str

    def __init__(  # noqa: D107, ANN204
        self,
        name: str,
        config: Dict,
        connection_str: Optional[str],
        message: str,
        event_bus: events.EventBus,
        id: UniqueId,  # noqa: A002
        *args,  # noqa: ANN002
        **kwargs,  # noqa: ANN003
    ):
        unit_of_work.UnitOfWork.__init__(self, event_bus)
        entity.TimestampedEntity.__init__(self, *args, id=id, **kwargs)
        self._name = name
        self._connection_str = connection_str
        self._config = config
        self._message = message

    @property
    def entries(self) -> EntryRepository:  # noqa: D102
        return self.repo

    @property
    def name(self) -> str:  # noqa: D102
        return self._name

    @property
    def connection_str(self) -> Optional[str]:  # noqa: D102
        return self._connection_str

    @property
    def config(self) -> Dict:  # noqa: D102
        return self._config

    @property
    def message(self) -> str:  # noqa: D102
        return self._message

    def discard(self, *, user, timestamp: Optional[float] = None):  # noqa: ANN201, D102
        self._discarded = True
        self._last_modified = self._ensure_timestamp(timestamp)
        self._last_modified_by = user
        # return entity.TimestampedEntity.discard(self, user=user, timestamp=timestamp)
        return []
