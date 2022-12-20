import logging
import typing

from karp.foundation.value_objects.permission_level import PermissionLevel

logger = logging.getLogger(__name__)


class User:
    def __init__(
        self,
        identifier: str,
        permissions: typing.Dict[str, int],
        levels: typing.Dict[str, int],
    ):
        self._identifier = identifier
        self._permissions = permissions
        self._levels = levels

    @property
    def identifier(self) -> str:
        return self._identifier

    def has_enough_permissions(self, resource_id: str, level: PermissionLevel) -> bool:
        try:
            return (self._permissions.get(resource_id) is not None) and (
                self._permissions[resource_id] >= self._levels[level]
            )
        except KeyError:
            logger.exception(
                "error checking permissions",
                extra={
                    "resource_id": resource_id,
                    "level": level,
                    "identifier": self._identifier,
                    "levels": self._levels,
                    "permissions": self._permissions,
                },
            )
            raise
