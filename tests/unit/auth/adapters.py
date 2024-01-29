from karp.auth import PermissionLevel
from karp.auth_infrastructure import LexIsResourceProtected


class InMemoryIsResourceProtected(LexIsResourceProtected):
    def __init__(self):
        pass

    def query(self, resource_id: str, level: PermissionLevel) -> bool:
        return True
