from typing import Optional  # noqa: I001
import elasticsearch
import injector
import logging

from karp.search_infrastructure.queries import (
    EsSearchService,
)
from karp.search_infrastructure.repositories.es_indices import EsIndex
from karp.search_infrastructure.es import EsMappingRepository


logger = logging.getLogger(__name__)


class EsSearchIndexMod(injector.Module):
    def __init__(self, index_prefix: Optional[str] = None) -> None:
        self._index_prefix = index_prefix or ""

    @injector.provider
    @injector.singleton
    def es_mapping_repo(
        self,
        es: elasticsearch.Elasticsearch,
    ) -> EsMappingRepository:
        return EsMappingRepository(es=es, prefix=self._index_prefix)

    @injector.provider
    def es_search_service(
        self,
        es: elasticsearch.Elasticsearch,
        mapping_repo: EsMappingRepository,
    ) -> EsSearchService:
        return EsSearchService(
            es=es,
            mapping_repo=mapping_repo,
        )

    @injector.provider
    def es_index(
        self,
        es: elasticsearch.Elasticsearch,
        mapping_repo: EsMappingRepository,
    ) -> EsIndex:
        return EsIndex(
            es=es,
            mapping_repo=mapping_repo,
        )
