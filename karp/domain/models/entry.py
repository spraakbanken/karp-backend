"""Model for a lexical entry."""
import abc
import enum
from functools import singledispatch
import logging
from typing import Dict, Optional, List
from uuid import UUID
from abc import abstractclassmethod

from karp.domain import constraints
from karp.domain.errors import ConfigurationError
from karp.domain.common import _now, _unknown_user
from karp.domain.models import event_handler
from karp.domain.models.entity import TimestampedVersionedEntity

from karp.utility import unique_id


_logger = logging.getLogger("karp")


class EntryOp(enum.Enum):
    ADDED = "ADDED"
    DELETED = "DELETED"
    UPDATED = "UPDATED"


class EntryStatus(enum.Enum):
    IN_PROGRESS = "IN-PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    OK = "OK"


class Entry(TimestampedVersionedEntity):
    class Discarded(TimestampedVersionedEntity.Discarded):
        def mutate(self, entry):
            super().mutate(entry)
            entry._op = EntryOp.DELETED
            entry._message = "Entry deleted." if self.message is None else self.message

    def __init__(
        self,
        entry_id: str,
        body: Dict,
        message: str,
        status: EntryStatus,  # IN-PROGRESS, IN-REVIEW, OK, PUBLISHED
        op: EntryOp,
        *pos,
        **kwargs,
        # version: int = 0
    ):
        super().__init__(*pos, **kwargs)
        self._entry_id = entry_id
        self._body = body
        self._op = op
        self._message = "Entry added." if message is None else message
        self._status = status

    @property
    def entry_id(self):
        """The entry_id of this entry."""
        return self._entry_id

    @entry_id.setter
    def entry_id(self, entry_id: str):
        self._check_not_discarded()
        self._entry_id = constraints.length_gt_zero("entry_id", entry_id)

    @property
    def body(self):
        """The body of the entry."""
        return self._body

    @body.setter
    def body(self, body: Dict):
        self._check_not_discarded()
        self._body = body

    @property
    def op(self):
        """The latest operation of this entry."""
        return self._op

    @property
    def status(self):
        """The workflow status of this entry."""
        return self._status

    @status.setter
    def status(self, status: EntryStatus):
        """The workflow status of this entry."""
        self._check_not_discarded()
        self._status = status

    @property
    def message(self):
        """The message for the latest operation of this entry."""
        return self._message

    def discard(self, *, user: str, message: str = None):
        event = Entry.Discarded(
            entity_id=self.id,
            entity_last_modified=self.last_modified,
            user=user,
            message=message,
            entity_version=self.version,
        )
        event.mutate(self)
        event_handler.publish(event)

    def stamp(
        self,
        user: str,
        *,
        message: str = None,
        timestamp: float = _now,
        increment_version: bool = True,
    ):
        super().stamp(user, timestamp=timestamp, increment_version=increment_version)
        self._message = message
        self._op = EntryOp.UPDATED


# === Factories ===
def create_entry(
    entry_id: str,
    body: Dict,
    *,
    last_modified_by: str = None,
    message: Optional[str] = None,
) -> Entry:
    if not isinstance(entry_id, str):
        entry_id = str(entry_id)
    entry = Entry(
        entry_id=entry_id,
        body=body,
        message="Entry added." if not message else message,
        status=EntryStatus.IN_PROGRESS,
        op=EntryOp.ADDED,
        entity_id=unique_id.make_unique_id(),
        version=1,
        last_modified_by="Unknown user" if not last_modified_by else last_modified_by,
    )
    return entry


# === Repository ===
class EntryRepository(metaclass=abc.ABCMeta):
    class Repository:
        def __init_subclass__(cls) -> None:
            print(f"Setting EntryRepository.repository = {cls}")
            EntryRepository.repository = cls

        def by_id(id: UUID):
            raise NotImplementedError()

    _registry = {}
    type = None
    repository = None

    def __init_subclass__(
        cls, repository_type: str, is_default: bool = False, **kwargs
    ) -> None:
        super().__init_subclass__(**kwargs)
        print(
            f"EntryRepository.__init_subclass__ called with repository_type={repository_type} and is_default={is_default}"
        )
        if repository_type is None:
            raise RuntimeError("Unallowed repository_type: repository_type = None")
        if repository_type in cls._registry:
            raise RuntimeError(
                f"An EntryRepository with type '{repository_type}' already exists: {cls._registry[repository_type]!r}"
            )

        # if is_default and None in cls._registry:
        #     raise RuntimeError(f"A default EntryRepository is already set. Default type is {cls._registry[None]!r}")
        cls.type = repository_type
        cls._registry[repository_type] = cls
        if is_default:
            if None in cls._registry:
                _logger.warn(
                    "Setting default EntryRepository type to '%s'", repository_type
                )
            cls._registry[None] = repository_type
        if None not in cls._registry:
            cls._registry[None] = repository_type

    @classmethod
    def get_default_repository_type(cls) -> Optional[str]:
        return cls._registry[None]

    @classmethod
    def create(cls, repository_type: Optional[str], settings: Dict):
        print(f"_registry={cls._registry}")
        if repository_type is None:
            repository_type = cls._registry[None]
        try:
            repository_cls = cls._registry[repository_type]
        except KeyError:
            raise ConfigurationError(
                f"Can't create an EntryRepository with type '{repository_type}'"
            )
        return repository_cls.from_dict(settings)

    @classmethod
    def create_repository_settings(
        cls, repository_type: Optional[str], resource_id: str
    ) -> Dict:
        if repository_type is None:
            repository_type = cls.get_default_repository_type()
        repository_cls = cls._registry[repository_type]
        return repository_cls._create_repository_settings(resource_id)

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, settings: Dict):
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def _create_repository_settings(cls, resource_id: str):
        raise NotImplementedError()

    @abc.abstractmethod
    def put(self, entry: Entry):
        raise NotImplementedError()

    @abc.abstractmethod
    def entry_ids(self) -> List[str]:
        raise NotImplementedError()

    @abc.abstractmethod
    def by_entry_id(self, entry_id: str) -> Optional[Entry]:
        raise NotImplementedError()

    @abc.abstractmethod
    def teardown(self):
        """Use for testing purpose."""
        return

    @abc.abstractmethod
    def by_referencable(self, **kwargs) -> List[Entry]:
        raise NotImplementedError()


class EntryRepositorySettings:
    """Settings for an EntryRepository."""

    pass


@singledispatch
def create_entry_repository(settings: EntryRepositorySettings) -> EntryRepository:
    raise RuntimeError(f"Don't know how to handle {settings!r}")
