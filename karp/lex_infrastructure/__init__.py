import injector
from sqlalchemy.engine import Connection

from karp.lex.application.queries import (
    GetPublishedResources,
    ResourceDto,
    ListEntryRepos,
    EntryRepoDto,
)

from karp.lex_infrastructure.queries import (
    SqlGetPublishedResources,
    SqlListEntryRepos,
)


class LexInfrastructure(injector.Module):
    @injector.provider
    def get_published_resources(self, conn: Connection) -> GetPublishedResources:
        return SqlGetPublishedResources(conn)

    @injector.provider
    def list_entry_repos(self, conn: Connection) -> ListEntryRepos:
        return SqlListEntryRepos(conn)
