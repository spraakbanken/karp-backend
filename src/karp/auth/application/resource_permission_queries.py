import typing

from karp.auth.domain.user import User
from karp.foundation.value_objects.permission_level import PermissionLevel
from karp.lex.infrastructure.sql import resource_repository


def _is_resource_protected(resource_id: str, level: PermissionLevel) -> bool:
    if level in [PermissionLevel.write, PermissionLevel.admin]:
        return True
    resource = resource_repository.by_resource_id(resource_id=resource_id)
    return resource.config.protected


def has_permission(
    level: PermissionLevel,
    user: User,
    resource_ids: typing.List[str],
) -> bool:
    return not any(
        _is_resource_protected(resource_id, level) and (not user or not user.has_enough_permissions(resource_id, level))
        for resource_id in resource_ids
    )
