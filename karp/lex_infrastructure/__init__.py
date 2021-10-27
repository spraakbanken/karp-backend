import injector
from sqlalchemy.engine import Connection

from karp.lex.application.queries import GetPublishedResources, ResourceDto

from karp.lex_infrastructure.queries import SqlGetPublishedResources


class LexInfrastructure(injector.Module):
    @injector.provider
    def get_published_resources(self, conn: Connection) -> GetPublishedResources:
        return SqlGetPublishedResources(conn)
