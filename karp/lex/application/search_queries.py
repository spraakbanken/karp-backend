from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, List

from injector import inject

from karp.foundation.json import get_path
from karp.lex.infrastructure import ResourceRepository
from karp.plugins import INDEXED, Plugins, expansion_phases, transform_list
from karp.search.domain import QueryRequest
from karp.search.infrastructure.es.search_service import EsSearchService


@dataclass
class _Result:
    path: str
    result: dict


class SearchQueries:
    """
    Implements search queries via ElasticSearch.

    Takes care of expanding plugins when results are fetched.
    """

    @inject
    def __init__(self, search: EsSearchService, resource_repository: ResourceRepository, plugins: Plugins):
        self.search = search
        self.resources = resource_repository
        self.plugins = plugins

    def _transform_result(self, path, result, expand_plugins=True):
        return self._transform_results([_Result(path, result)], expand_plugins)[0]

    def _transform_results(self, results, expand_plugins=True):
        phases = expansion_phases(expand_plugins, start=INDEXED)

        # We need to expand separately per resource
        results = list(results)
        hits_by_resource = defaultdict(list)
        for i, result in enumerate(results):
            for j, hit in enumerate(result.result["hits"]):
                hits_by_resource[hit["resource"]].append((i, j))

        for resource, hit_ids in hits_by_resource.items():
            config = self.resources.by_resource_id(resource).config
            hits = [results[i].result["hits"][j]["entry"] for i, j in hit_ids]
            hits = transform_list(self.plugins, config, hits, expand_plugins=phases)
            for (i, j), hit in zip(hit_ids, hits):
                results[i].result["hits"][j]["entry"] = hit

        # Handle path field
        for result in results:
            if result.path:
                result.result["hits"] = [get_path(result.path, entry) for entry in result.result["hits"]]

        return [result.result for result in results]

    def query(self, query: QueryRequest, **kwargs):
        path = query.path
        query.path = None  # we need the full path to expand plugins
        result = self.search.query(query)
        return self._transform_result(path, result, **kwargs)

    def query_stats(self, resources, q):
        return self.search.query_stats(resources, q)

    def multi_query(self, queries: list[QueryRequest], **kwargs):
        queries = list(queries)
        paths = [q.path for q in queries]
        for q in queries:
            q.path = None
        results = self.search.multi_query(queries)
        return self._transform_results([_Result(p, r) for p, r in zip(paths, results)], **kwargs)

    def search_ids(self, resource_id: str, entry_ids: List[str], **kwargs):
        result = self.search.search_ids(resource_id, entry_ids)
        return self._transform_result(None, result, **kwargs)

    def statistics(self, resource_id: str, field: str) -> Iterable:
        return self.search.statistics(resource_id, field)
