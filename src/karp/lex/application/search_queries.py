from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, List

from karp.foundation.json import get_path
from karp.globals import es_search_service
from karp.lex.infrastructure.sql import resource_repository
from karp.plugins import INDEXED, expansion_phases, transform_list
from karp.search.domain import QueryRequest


@dataclass
class _Result:
    path: str
    result: dict


"""
Implements search queries via ElasticSearch.

Takes care of expanding plugins when results are fetched.
"""


def _transform_result(path, result, expand_plugins=True):
    return _transform_results([_Result(path, result)], expand_plugins)[0]


def _transform_results(results, expand_plugins=True):
    phases = expansion_phases(expand_plugins, start=INDEXED)

    # We need to expand separately per resource
    results = list(results)
    hits_by_resource = defaultdict(list)
    for i, result in enumerate(results):
        for j, hit in enumerate(result.result["hits"]):
            hits_by_resource[hit["resource"]].append((i, j))

    for resource, hit_ids in hits_by_resource.items():
        config = resource_repository.by_resource_id(resource).config
        hits = [results[i].result["hits"][j]["entry"] for i, j in hit_ids]
        hits = transform_list(config, hits, expand_plugins=phases)
        for (i, j), hit in zip(hit_ids, hits, strict=False):
            results[i].result["hits"][j]["entry"] = hit

    # Handle path field
    for result in results:
        if result.path:
            result.result["hits"] = [get_path(result.path, entry) for entry in result.result["hits"]]

    return [result.result for result in results]


def query(query: QueryRequest, **kwargs):
    path = query.path
    query.path = None  # we need the full path to expand plugins
    result = es_search_service.query(query)
    return _transform_result(path, result, **kwargs)


def query_stats(resources, q):
    return es_search_service.query_stats(resources, q)


def multi_query(queries: list[QueryRequest], **kwargs):
    queries = list(queries)
    paths = [q.path for q in queries]
    for q in queries:
        q.path = None
    results = es_search_service.multi_query(queries)
    return _transform_results([_Result(p, r) for p, r in zip(paths, results, strict=False)], **kwargs)


def search_ids(resource_id: str, entry_ids: List[str], **kwargs):
    result = es_search_service.search_ids(resource_id, entry_ids)
    return _transform_result(None, result, **kwargs)


def statistics(resource_id: str, field: str) -> Iterable:
    return es_search_service.statistics(resource_id, field)
