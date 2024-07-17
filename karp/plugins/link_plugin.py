from injector import Injector, inject

from karp.lex.application import ResourceQueries
from karp.search.domain import QueryRequest
from karp.search.infrastructure import EsSearchService

from .plugin import Plugin


class LinkPlugin(Plugin):
    @inject
    def __init__(self, resources: ResourceQueries, search_service: EsSearchService):
        self.resources = resources
        self.search_service = search_service

    def output_config(self, resource, target):
        resource_dto = self.resources.by_resource_id_optional(resource)
        if resource_dto:
            return {"type": "object", "fields": resource_dto.config.fields}
        else:
            # Return no fields for now - the user must run 'karp-cli resource reindex' later
            return {"type": "object", "fields": {}}

    def generate_batch(self, batch):
        def make_request(id, resource, target):  # noqa: A002
            return QueryRequest(
                resources=[resource], q=f"equals|{target}|\"{id}\"", lexicon_stats=False
            )

        requests = [make_request(**d) for d in batch]
        results = self.search_service.multi_query(requests)

        for result in results:
            hits = result["hits"]

            if len(hits) == 0:
                # TODO: how to communicate errors?
                yield {"error": "not found"}
            elif len(hits) == 1:
                yield hits[0]["entry"]
            else:
                yield {"error": "multiple matches"}
