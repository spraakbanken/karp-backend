from typing import Optional  # noqa: I001
import elasticsearch
import injector
import logging

from karp.lex.application.repositories import ResourceRepository

from karp.search_infrastructure.queries import (
    Es6SearchService,
)
from karp.search_infrastructure.repositories.es6_indicies import Es6Index
from karp.search_infrastructure.elasticsearch6 import Es6MappingRepository
from karp.search.generic_resources import GenericResourceViews


logger = logging.getLogger(__name__)


class GenericSearchInfrastructure(injector.Module):  # noqa: D101
    @injector.provider
    def get_resource_config(self, resources: ResourceRepository) -> GenericResourceViews:
        return GenericResourceViews(resources=resources)


class Es6SearchIndexMod(injector.Module):  # noqa: D101
    def __init__(self, index_prefix: Optional[str] = None) -> None:  # noqa: D107
        self._index_prefix = index_prefix or ""

    @injector.provider
    @injector.singleton
    def es6_mapping_repo(  # noqa: D102
        self,
        es: elasticsearch.Elasticsearch,
    ) -> Es6MappingRepository:
        return Es6MappingRepository(es=es, prefix=self._index_prefix)

    @injector.provider
    def es6_search_service(  # noqa: D102
        self,
        es: elasticsearch.Elasticsearch,
        mapping_repo: Es6MappingRepository,
    ) -> Es6SearchService:
        return Es6SearchService(
            es=es,
            mapping_repo=mapping_repo,
        )

    @injector.provider
    def es6_index(
        self,
        es: elasticsearch.Elasticsearch,
        mapping_repo: Es6MappingRepository,
    ) -> Es6Index:
        return Es6Index(
            es=es,
            mapping_repo=mapping_repo,
        )
