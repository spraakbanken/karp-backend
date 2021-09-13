from dependency_injector import containers, providers

from karp.domain.index import Index as SearchService


class SearchServiceProvider(providers.Factory):

    provided_type = SearchService
