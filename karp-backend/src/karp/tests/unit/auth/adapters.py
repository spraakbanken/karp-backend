from karp.auth.application.queries import IsResourceProtected
from karp.auth import PermissionLevel


class InMemoryIsResourceProtected(IsResourceProtected):
    def query(self, resource_id: str, level: PermissionLevel) -> bool:
        return super().query(resource_id, level)
