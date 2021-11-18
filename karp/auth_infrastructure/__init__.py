import injector

from karp.auth.domain.auth_service import AuthService
from karp.auth.application.queries import GetResourcePermissions
from karp.auth_infrastructure.queries import LexGetResourcePermissions
from karp.auth_infrastructure.services import DummyAuthService
from karp.lex.application import repositories as lex_repositories


class AuthInfrastructure(injector.Module):
    @injector.provider
    def resource_permissions(
        self,
        resource_uow: lex_repositories.ResourceUnitOfWork,
    ) -> GetResourcePermissions:
        return LexGetResourcePermissions(resource_uow)


class TestAuthInfrastructure(injector.Module):
    @injector.provider
    def dummy_auth_service(self) -> AuthService:
        return DummyAuthService()
