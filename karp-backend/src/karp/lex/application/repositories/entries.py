from typing import Dict, List, Optional, Tuple

from karp.foundation import entity, repository
from karp.lex_core.value_objects import UniqueId


class EntryRepository(  # noqa: D101
    entity.TimestampedEntity,
    repository.Repository,
):
    def __init__(  # noqa: D107, ANN204
        self,
        name: str,
        config: Dict,
        message: str,
        id: UniqueId,  # noqa: A002
        *args,  # noqa: ANN002
        **kwargs,  # noqa: ANN003
    ):
        repository.Repository.__init__(self)
        entity.TimestampedEntity.__init__(self, *args, id=id, **kwargs)
        self._name = name
        self._config = config
        self._message = message

    @property
    def name(self) -> str:  # noqa: D102
        return self._name

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
        return []
