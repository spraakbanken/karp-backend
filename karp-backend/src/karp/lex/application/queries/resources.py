import abc  # noqa: D100, I001
from typing import Iterable, Optional


from karp.lex_core.value_objects import UniqueId
from karp.lex_core.value_objects.unique_id import UniqueIdPrimitive
from karp.lex.application.dtos import ResourceDto


class GetPublishedResources(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def query(self) -> Iterable[ResourceDto]:  # noqa: D102
        pass


class GetResources(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def query(self) -> Iterable[ResourceDto]:  # noqa: D102
        pass


class GetEntryRepositoryId(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def query(self, resource_id: str) -> UniqueId:  # noqa: D102
        raise NotImplementedError()


class ReadOnlyResourceRepository(abc.ABC):  # noqa: D101
    def get_by_resource_id(  # noqa: D102
        self, resource_id: str, version: Optional[int] = None
    ) -> Optional[ResourceDto]:
        resource = self._get_by_resource_id(resource_id)
        if not resource:
            return None

        if version is not None:
            resource = self.get_by_id(resource.id, version=version)
        return resource

    @abc.abstractmethod
    def get_by_id(  # noqa: D102
        self, id: UniqueIdPrimitive, version: Optional[int] = None  # noqa: A002
    ) -> Optional[ResourceDto]:
        pass

    @abc.abstractmethod
    def _get_by_resource_id(self, resource_id: str) -> Optional[ResourceDto]:
        pass

    @abc.abstractmethod
    def get_published_resources(self) -> Iterable[ResourceDto]:  # noqa: D102
        pass
