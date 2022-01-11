from karp.foundation.value_objects.permission_level import PermissionLevel


class User:
    def __init__(self, identifier, permissions, levels):
        self._identifier = identifier
        self._permissions = permissions
        self._levels = levels

    @property
    def identifier(self):
        return self._identifier

    def has_enough_permissions(self, resource_id: str, level: PermissionLevel) -> bool:
        return self._permissions.get(resource_id) and (self._permissions[resource_id] >= self._levels[level])
