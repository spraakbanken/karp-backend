from pathlib import Path  # noqa: I001
import injector

from karp.auth_infrastructure.queries import (
    ResourcePermissionQueries,
)
from karp.auth_infrastructure.services import (
    JWTAuthService,
)
from karp.lex.application.repositories import ResourceRepository


class AuthInfrastructure(injector.Module):  # noqa: D101
    @injector.provider
    def resource_permissions(  # noqa: D102
        self, resources: ResourceRepository
    ) -> ResourcePermissionQueries:
        return ResourcePermissionQueries(resources)


class JwtAuthInfrastructure(injector.Module):  # noqa: D101
    def __init__(self, pubkey_path: Path) -> None:  # noqa: D107
        super().__init__()
        self.pubkey_path = pubkey_path

    @injector.provider
    def jwt_auth_service(self) -> JWTAuthService:
        return JWTAuthService(pubkey_path=self.pubkey_path)
