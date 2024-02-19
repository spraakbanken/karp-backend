from typing import Optional  # noqa: I001
import elasticsearch
import injector
import logging

from karp.search_infrastructure.queries import (
    Es6SearchService,
)
from karp.search_infrastructure.repositories.es6_indicies import Es6Index
from karp.search_infrastructure.elasticsearch6 import Es6MappingRepository


logger = logging.getLogger(__name__)


class Es6SearchIndexMod(injector.Module):
    def __init__(self, index_prefix: Optional[str] = None) -> None:
        self._index_prefix = index_prefix or ""

    @injector.provider
    @injector.singleton
    def es6_mapping_repo(
        self,
        es: elasticsearch.Elasticsearch,
    ) -> Es6MappingRepository:
        return Es6MappingRepository(es=es, prefix=self._index_prefix)

    @injector.provider
    def es6_search_service(
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
