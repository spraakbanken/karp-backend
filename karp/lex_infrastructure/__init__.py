import logging  # noqa: I001

import injector
from sqlalchemy.orm import Session

from karp.lex_infrastructure.queries import (
    EntryQueries,
    ResourceQueries,
)
from karp.lex_infrastructure.repositories import (
    SqlResourceRepository,
)
from karp.lex.application.repositories import ResourceRepository

logger = logging.getLogger(__name__)


class LexInfrastructure(injector.Module):  # noqa: D101
    @injector.provider
    def resources(  # noqa: D102
        self,
        session: Session,
    ) -> ResourceRepository:
        return SqlResourceRepository(
            session=session,
        )


class GenericLexInfrastructure(injector.Module):  # noqa: D101
    @injector.provider
    def resource_queries(  # noqa: D102
        self, resources: ResourceRepository
    ) -> ResourceQueries:
        return ResourceQueries(resources)

    @injector.provider
    def entry_queries(  # noqa: D102
        self,
        resources: ResourceRepository,
    ) -> EntryQueries:
        return EntryQueries(
            resources=resources,
        )
