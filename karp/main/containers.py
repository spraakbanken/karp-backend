import logging.config

import elasticsearch
from dependency_injector import containers, providers

from karp import db_infrastructure
from karp.search_infrastructure import elasticsearch6
from karp.search_infrastructure.sql.sql_search_service import SqlSearchService
from karp.search_infrastructure.sql.unit_of_work import SqlSearchServiceUnitOfWork
from karp.auth_infrastructure.jwt import jwt_auth_service
from karp.lex_infrastructure.sql import sql_unit_of_work
from karp.lex.application import unit_of_work
from .bootstrap import bootstrap_message_bus


class Core(containers.DeclarativeContainer):

    config = providers.Configuration()

    logging = providers.Resource(
        logging.config.dictConfig,
        config=config.logging,
    )


class AppContainer(containers.DeclarativeContainer):

    config = providers.Configuration()

    core = providers.Container(
        Core,
        config=config.core,
    )
    db = providers.Singleton(db_infrastructure.Database, db_url=config.db.url)

    resource_uow = providers.Singleton(
        sql_unit_of_work.SqlResourceUnitOfWork,
        session_factory=db.provided.session_factory,
    )

    entry_uows = providers.Singleton(unit_of_work.EntriesUnitOfWork)

    # entry_uow_factory = providers.Singleton(unit_of_work.DefaultEntryUowFactory)

    es6 = providers.Singleton(
        elasticsearch.Elasticsearch, hosts=config.search_service.elasticsearch_hosts
    )

    es6_search_service = providers.Singleton(
        elasticsearch6.es6_search_service.Es6SearchService, es=es6.provided
    )

    es6_search_service_uow = providers.Singleton(
        elasticsearch6.es6_unit_of_work.Es6SearchServiceUnitOfWork,
        es6_search_service=es6_search_service.provided,
    )

    sql_search_service_uow = providers.Singleton(
        SqlSearchServiceUnitOfWork,
        session_factory=db.provided.session_factory,
    )

    search_service_uow = providers.Selector(
        config.search_service.type,
        es6_search_service=es6_search_service_uow,
        sql_search_service=sql_search_service_uow,
    )

    bus = providers.Singleton(
        bootstrap_message_bus,
        resource_uow=resource_uow.provided,
        entry_uows=entry_uows.provided,
        search_service_uow=search_service_uow.provided,
        entry_uow_factory=entry_uow_factory.provided,
        raise_on_all_errors=config.debug,
    )

#    jwt_authenticator = providers.Singleton(
#        jwt_auth_service.JWTAuthenticator,
#        pubkey_path=config.auth.jwt.pubkey_path,
#        resource_uow=resource_uow,
#    )
#
#    auth_service = providers.Selector(config.auth.type, jwt_auth=jwt_authenticator)
