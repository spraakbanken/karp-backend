from typing import Dict
import injector
from sqlalchemy.engine import Connection
from sqlalchemy.orm import sessionmaker

from karp.lex.application.queries import (
    GetPublishedResources,
    ResourceDto,
    ListEntryRepos,
    EntryRepoDto,
)
from karp.lex.application.repositories import (
    EntryUowRepositoryUnitOfWork,
    EntryUnitOfWorkCreator,
)
from karp.lex_infrastructure.queries import (
    SqlGetPublishedResources,
    SqlListEntryRepos,
)
from karp.lex_infrastructure.repositories import (
    SqlEntryUowRepositoryUnitOfWork,
    SqlEntryUowCreator,
)


class LexInfrastructure(injector.Module):
    @injector.provider
    def get_published_resources(self, conn: Connection) -> GetPublishedResources:
        return SqlGetPublishedResources(conn)

    @injector.provider
    def list_entry_repos(self, conn: Connection) -> ListEntryRepos:
        return SqlListEntryRepos(conn)

    @injector.provider
    def entry_uow_repo(self, session_factory: sessionmaker) -> EntryUowRepositoryUnitOfWork:
        return SqlEntryUowRepositoryUnitOfWork(session_factory)

    @injector.multiprovider
    def entry_uow_creator_map(self) -> Dict[str, EntryUnitOfWorkCreator]:
        return {
            'default': SqlEntryUowCreator,
            'sql_entries': SqlEntryUowCreator,
        }
