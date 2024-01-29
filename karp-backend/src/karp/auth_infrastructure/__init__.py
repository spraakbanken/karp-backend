from pathlib import Path  # noqa: I001
import injector

from karp.auth_infrastructure.queries import (
    LexGetResourcePermissions,
    LexIsResourceProtected,
)
from karp.auth_infrastructure.services import (
    JWTAuthService,
    JWTAuthServiceConfig,
)
from karp.lex_infrastructure import SqlGetPublishedResources, SqlReadOnlyResourceRepository


class AuthInfrastructure(injector.Module):  # noqa: D101
    @injector.provider
    def resource_permissions(  # noqa: D102
        self, get_published_resources: SqlGetPublishedResources
    ) -> LexGetResourcePermissions:
        return LexGetResourcePermissions(get_published_resources)

    @injector.provider
    def is_resource_protected(  # noqa: D102
        self, resource_repo: SqlReadOnlyResourceRepository
    ) -> LexIsResourceProtected:
        return LexIsResourceProtected(resource_repo)


class JwtAuthInfrastructure(injector.Module):  # noqa: D101
    def __init__(self, pubkey_path: Path) -> None:  # noqa: D107
        super().__init__()
        self.pubkey_path = pubkey_path

    @injector.provider
    @injector.singleton
    def jwt_auth_service_config(self) -> JWTAuthServiceConfig:  # noqa: D102
        return JWTAuthServiceConfig(self.pubkey_path)

    @injector.provider
    def jwt_auth_service(  # noqa: D102
        self, is_resource_protected: LexIsResourceProtected
    ) -> JWTAuthService:
        return JWTAuthService(
            pubkey_path=self.pubkey_path, is_resource_protected=is_resource_protected
        )
