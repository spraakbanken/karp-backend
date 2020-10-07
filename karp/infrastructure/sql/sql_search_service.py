from karp.domain.models.search_service import SearchService


class SqlSearchService(SearchService, search_service_type="sql_search_service", is_default=True):
    pass
