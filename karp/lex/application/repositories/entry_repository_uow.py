import abc
from typing import Dict

from karp.foundation.value_objects import UniqueId
from .unit_of_work import EntryUnitOfWork


class EntryRepositoryUnitOfWorkFactory:
    @abc.abstractmethod
    def create(
        self,
        repository_type: str,
        entity_id: UniqueId,
        name: str,
        config: Dict,
    ) -> EntryUnitOfWork:
        pass
