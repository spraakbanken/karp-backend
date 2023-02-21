from pathlib import Path  # noqa: I001
import injector

from karp.auth import (
    AuthService,
    AuthServiceConfig,
    GetResourcePermissions,
    IsResourceProtected,
)
from karp.auth_infrastructure.queries import (
    LexGetResourcePermissions,
    LexIsResourceProtected,
)
from karp.auth_infrastructure.services import (
    DummyAuthService,
    JWTAuthService,
    JWTAuthServiceConfig,
)
from karp.lex.application.queries import (
    GetPublishedResources,
    ReadOnlyResourceRepository,
)


class AuthInfrastructure(injector.Module):  # noqa: D101
    @injector.provider
    def resource_permissions(  # noqa: D102
        self, get_published_resources: GetPublishedResources
    ) -> GetResourcePermissions:
        return LexGetResourcePermissions(get_published_resources)

    @injector.provider
    def is_resource_protected(  # noqa: D102
        self, resource_repo: ReadOnlyResourceRepository
    ) -> IsResourceProtected:
        return LexIsResourceProtected(resource_repo)


class TestAuthInfrastructure(injector.Module):  # noqa: D101
    @injector.provider
    def dummy_auth_service(self) -> AuthService:  # noqa: D102
        return DummyAuthService()


class JwtAuthInfrastructure(injector.Module):  # noqa: D101
    def __init__(self, pubkey_path: Path) -> None:  # noqa: D107
        super().__init__()
        self.pubkey_path = pubkey_path

    @injector.provider
    @injector.singleton
    def jwt_auth_service_config(self) -> AuthServiceConfig:  # noqa: D102
        return JWTAuthServiceConfig(self.pubkey_path)

    @injector.provider
    def jwt_auth_service(  # noqa: D102
        self, is_resource_protected: IsResourceProtected
    ) -> AuthService:
        return JWTAuthService(
            pubkey_path=self.pubkey_path, is_resource_protected=is_resource_protected
        )
