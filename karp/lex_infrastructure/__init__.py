import logging  # noqa: I001

import injector
from sqlalchemy.orm import Session

from karp.lex.application import (
    EntryQueries,
    ResourceQueries,
)
from .sql import ResourceRepository, EntryRepository


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

__all__ = [
    "LexInfrastructure",
    "GenericLexInfrastructure",
    "ResourceRepository",
    "EntryRepository",
]
