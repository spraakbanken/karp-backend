from . import errors  # noqa: F401
from .search import Query, SearchInterface  # noqa: F401

_search = None


def build_query(args, resource_str: str) -> Query:
    if _search is None:
        raise RuntimeError("karp.search isn't initalized.")
    return _search.build_query(args, resource_str)


def search_with_query(query: Query):
    if _search is None:
        raise RuntimeError("karp.search isn't initalized.")
    return _search.search_with_query(query)


def search_ids(args, resource_id: str, entry_ids: str):
    if _search is None:
        raise RuntimeError("karp.search isn't initalized.")
    return _search.search_ids(args, resource_id, entry_ids)


def statistics(resource_id: str, field: str):
    if _search is None:
        raise RuntimeError("karp.search isn't initalized.")
    return _search.statistics(resource_id, field)


def init(impl: SearchInterface):
    global _search
    _search = impl
