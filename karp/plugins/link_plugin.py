from injector import Injector, inject

from karp.lex.application import ResourceQueries
from karp.search.domain import QueryRequest
from karp.search.infrastructure import EsSearchService

from .plugin import Plugin, register_plugin


class LinkPlugin(Plugin):
    @inject
    def __init__(self, resources: ResourceQueries, search_service: EsSearchService):
        self.resources = resources
        self.search_service = search_service

    def output_config(self, resource, target):
        resource_dto = self.resources.by_resource_id_optional(resource)
        return {"type": "object", "fields": resource_dto.config["fields"]}

    def generate(self, id, resource, target):  # noqa: A002
        if isinstance(id, list):
            return [self.generate(x, resource, target) for x in id]

        query = QueryRequest(
            resource_ids=[resource], q=f"equals|{target}|{id}", lexicon_stats=False
        )
        result = self.search_service.query(query)["hits"]

        if len(result) == 0:
            return {"error": "not found"}
        elif len(result) == 1:
            return result[0]["entry"]
        else:
            return {"error": "multiple matches"}


register_plugin(LinkPlugin)
