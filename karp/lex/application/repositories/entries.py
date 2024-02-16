from typing import Dict, List, Optional, Tuple

from karp.foundation import entity, repository
from karp.lex_core.value_objects import UniqueId


class EntryRepository(
    entity.TimestampedEntity,
    repository.Repository,
):
    def __init__(
        self,
        name: str,
        config: Dict,
        message: str,
        id: UniqueId,  # noqa: A002
        *args,
        **kwargs,
    ):
        repository.Repository.__init__(self)
        entity.TimestampedEntity.__init__(self, *args, id=id, **kwargs)
        self._name = name
        self._config = config
        self._message = message

    @property
    def name(self) -> str:
        return self._name

    @property
    def config(self) -> Dict:
        return self._config

    @property
    def message(self) -> str:
        return self._message

    def discard(self, *, user, timestamp: Optional[float] = None):
        self._discarded = True
        self._last_modified = self._ensure_timestamp(timestamp)
        self._last_modified_by = user
        return []
