import logging  # noqa: I001

import injector
from sqlalchemy.orm import Session

from karp.lex_infrastructure.queries import (
    EntryQueries,
    ResourceQueries,
)
from karp.lex_infrastructure.repositories import ResourceRepository


logger = logging.getLogger(__name__)


class LexInfrastructure(injector.Module):
    @injector.provider
    def resources(
        self,
        session: Session,
    ) -> ResourceRepository:
        return ResourceRepository(
            session=session,
        )


class GenericLexInfrastructure(injector.Module):
    @injector.provider
    def resource_queries(self, resources: ResourceRepository) -> ResourceQueries:
        return ResourceQueries(resources)

    @injector.provider
    def entry_queries(
        self,
        resources: ResourceRepository,
    ) -> EntryQueries:
        return EntryQueries(
            resources=resources,
        )
