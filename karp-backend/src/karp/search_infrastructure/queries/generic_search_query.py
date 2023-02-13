import typing

from karp.lex.application.repositories import ResourceUnitOfWork
from karp.search.application.queries import SearchQuery
from karp.search.application.repositories import SearchServiceUnitOfWork
from karp.search.domain import search_service, errors


class GenericSearchQuery(SearchQuery):
    def __init__(
        self,
        resource_uow: ResourceUnitOfWork,
        search_service_uow: SearchServiceUnitOfWork,
    ):
        self.resource_uow = resource_uow
        self.search_service_uow = search_service_uow

    def check_resource_published(self, resource_id: str):
        with self.resource_uow:
            resource = self.resource_uow.repo.by_resource_id(resource_id)
            if not resource.is_published:
                raise errors.ResourceNotPublished(resource_id)

    def check_all_resources_published(self, resource_ids: typing.Iterable[str]):
        with self.resource_uow:
            for resource_id in resource_ids:
                resource = self.resource_uow.repo.by_resource_id(resource_id)
                if not resource.is_published:
                    raise errors.ResourceNotPublished(resource_id)

    def search_ids(self, resource_id: str, entry_ids: str):
        self.check_resource_published(resource_id)
        with self.search_service_uow:
            return self.search_service_uow.repo.search_ids(resource_id, entry_ids)

    def query(self, req: search_service.QueryRequest):
        print(f"entry_query.query called with req={req}")
        self.check_all_resources_published(req.resource_ids)

        with self.search_service_uow:
            return self.search_service_uow.repo.query(req)

    def query_split(self, req: search_service.QueryRequest):
        self.check_all_resources_published(req.resource_ids)
        with self.search_service_uow as uw:
            return uw.repo.query_split(req)

    def statistics(self, resource_id: str, field: str):
        self.check_resource_published(resource_id)
        with self.search_service_uow as uw:
            return uw.repo.statistics(resource_id, field)
