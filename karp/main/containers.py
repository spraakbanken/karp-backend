import logging

from dependency_injector import containers, providers

from sqlalchemy import create_engine


from karp import db_infrastructure
from karp.services import unit_of_work
from karp.infrastructure.sql import sql_unit_of_work


class Core(containers.DeclarativeContainer):

    config = providers.Configuration()

    logging = providers.Resource(
        logging.config.dictConfig,
        config=config.logging,
    )


class AppContainer(containers.DeclarativeContainer):

    config = providers.Configuration()

    db = providers.Singleton(
        db_infrastructure.Database,
        db_url=config.db.url
    )

    resource_uow = providers.Singleton(
        sql_unit_of_work.SqlResourceUnitOfWork,

    )
    search_service = providers.Singleton()
