from dependency_injector import containers, providers

from karp.search_service.containers import SearchServiceProvider


class Es6SearchServiceProvider(containers.DeclarativeContainer):

    search_service = SearchServiceProvider()
