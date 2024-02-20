from pathlib import Path

import injector

from karp.auth.application.resource_permission_queries import ResourcePermissionQueries
from karp.auth.infrastructure.jwt_auth_service import JWTAuthService
from karp.lex.infrastructure import ResourceRepository


class AuthInfrastructure(injector.Module):
    @injector.provider
    def resource_permissions(self, resources: ResourceRepository) -> ResourcePermissionQueries:
        return ResourcePermissionQueries(resources)


class JwtAuthInfrastructure(injector.Module):
    def __init__(self, pubkey_path: Path) -> None:
        super().__init__()
        self.pubkey_path = pubkey_path

    @injector.provider
    def jwt_auth_service(self) -> JWTAuthService:
        return JWTAuthService(pubkey_path=self.pubkey_path)
