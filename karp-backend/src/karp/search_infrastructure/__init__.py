from typing import Optional  # noqa: I001
import elasticsearch
import injector
import logging

from karp import lex
from karp.lex_infrastructure import GenericEntryViews, SqlReadOnlyResourceRepository

from karp.search_infrastructure.queries import (
    Es6SearchService,
)
from karp.search_infrastructure.transformers import (
    GenericEntryTransformer,
    GenericPreProcessor,
)
from karp.search_infrastructure.repositories import (
    Es6IndexUnitOfWork,
)
from karp.search_infrastructure.elasticsearch6 import Es6MappingRepository
from karp.search.generic_resources import GenericResourceViews


logger = logging.getLogger(__name__)


class SearchInfrastructure(injector.Module):  # noqa: D101
    @injector.provider
    def entry_transformer(  # noqa: D102
        self,
        index_uow: Es6IndexUnitOfWork,
        resource_repo: SqlReadOnlyResourceRepository,
        entry_views: GenericEntryViews,
    ) -> GenericEntryTransformer:
        return GenericEntryTransformer(
            index_uow=index_uow,
            resource_repo=resource_repo,
            entry_views=entry_views,
        )

    @injector.provider
    def pre_processor(  # noqa: D102
        self,
        entry_transformer: GenericEntryTransformer,
        entry_views: GenericEntryViews,
    ) -> GenericPreProcessor:
        return GenericPreProcessor(
            entry_transformer=entry_transformer,
            entry_views=entry_views,
        )


class GenericSearchInfrastructure(injector.Module):  # noqa: D101
    @injector.provider
    def get_resource_config(  # noqa: D102
        self, resource_uow: lex.ResourceUnitOfWork
    ) -> GenericResourceViews:
        return GenericResourceViews(resource_uow=resource_uow)


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
    def es6_index_uow(
        self,
        es: elasticsearch.Elasticsearch,
        mapping_repo: Es6MappingRepository,
    ) -> Es6IndexUnitOfWork:
        return Es6IndexUnitOfWork(
            es=es,
            mapping_repo=mapping_repo,
        )
